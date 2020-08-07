# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils.functional import cached_property

from xyz_util.modelutils import CodeMixin
from django.contrib.auth.models import User, Group


class Teacher(CodeMixin, models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "老师"
        ordering = ('-create_time',)

    user = models.OneToOneField(User, verbose_name="网站用户", null=True, blank=True, related_name="as_school_teacher")
    name = models.CharField("姓名", max_length=32, db_index=True)
    code = models.CharField("拼音缩写", max_length=64, db_index=True, blank=True, default="")
    description = models.CharField("简介", max_length=256, blank=True, default="")
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    modify_time = models.DateTimeField("修改时间", auto_now=True)
    courses = models.ManyToManyField("course.course", verbose_name="课程", blank=True, through="ClassCourse",
                                     related_name="school_teachers")
    classes = models.ManyToManyField("Class", verbose_name="班级", blank=True, through="ClassCourse",
                                     related_name="teachers")

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        # if not self.user:
        #     self.user = self.party.workers.create(name=self.name, position=self._meta.verbose_name).user
        return super(Teacher, self).save(**kwargs)

    @cached_property
    def students(self):
        return Student.objects.filter(class_id__in=list(self.class_courses.values_list('class_id', flat=True)))


class Session(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "届别"
        ordering = ('number',)

    number = models.PositiveSmallIntegerField("编号", unique=True)
    name = models.CharField("名称", max_length=64, db_index=True, blank=True)
    begin_date = models.DateField("开始日期", blank=True)
    end_date = models.DateField("结束日期", blank=True)

    def save(self, **kwargs):
        if not self.name and self.number:
            self.name = "%s届" % self.number
        if self.name and not self.number:
            self.number = int(self.name.replace('届', ''))
        if not self.begin_date:
            self.begin_date = "%s-08-01" % self.number
        if not self.end_date:
            self.end_date = "%s-07-31" % (int(self.number) + 1)
        return super(Session, self).save(**kwargs)

    def __unicode__(self):
        return self.name


class Grade(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "年级"
        ordering = ('number',)

    number = models.PositiveSmallIntegerField("编号", default=1, unique=True)
    name = models.CharField("名称", max_length=64, db_index=True, blank=True)
    class_count = models.PositiveSmallIntegerField("班数", default=3)

    def save(self, **kwargs):
        if not self.name:
            n = self.number
            self.name = n <= 10 and '%s年级' % "零一二三四五六七八九十"[self.number] or '%d级' % n
        return super(Grade, self).save(**kwargs)

    def __unicode__(self):
        return self.name


class College(CodeMixin, models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "院系"
        ordering = ('name',)

    name = models.CharField("名称", max_length=64, db_index=True)
    code = models.CharField("拼音缩写", max_length=64, unique=True, blank=True, default="")
    short_name = models.CharField("简称", max_length=64, blank=True, default="", db_index=True)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    update_time = models.DateTimeField("修改时间", auto_now=True)

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        self.short_name = self.short_name or self.name
        return super(College, self).save(**kwargs)

    @cached_property
    def students(self):
        return Student.objects.filter(major__in=self.majors)

    @cached_property
    def student_count(self):
        return self.students.count()


class Major(CodeMixin, models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "专业"
        ordering = ("name",)

    name = models.CharField("名称", max_length=64, db_index=True)
    short_name = models.CharField("简称", max_length=64, blank=True, default="", db_index=True)
    code = models.CharField("拼音缩写", max_length=64, unique=True, blank=True, default="")
    college = models.ForeignKey(College, verbose_name="院系", related_name="majors", null=True, blank=True,
                                on_delete=models.PROTECT)
    study_years = models.PositiveSmallIntegerField("年制", blank=True, default=3)
    students = models.ManyToManyField('student', related_name="majors")
    courses = models.ManyToManyField("course.course", verbose_name="课程", blank=True,
                                     related_name="school_majors")
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    update_time = models.DateTimeField("修改时间", auto_now=True)

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        self.short_name = self.short_name or self.name
        return super(Major, self).save(**kwargs)

    @cached_property
    def student_count(self):
        return self.students.count()


class Class(CodeMixin, models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "班级"
        ordering = ('grade', 'name')

    name = models.CharField("名称", max_length=64, unique=True)
    short_name = models.CharField("简称", max_length=64, null=True, blank=True, db_index=True)
    code = models.CharField("拼音缩写", max_length=64, db_index=True, blank=True, default="")
    grade = models.ForeignKey(Grade, verbose_name=Grade._meta.verbose_name, related_name="classes", blank=True)
    entrance_session = models.ForeignKey(Session, verbose_name="入学届别", related_name="entrance_classes", blank=True)
    graduate_session = models.ForeignKey(Session, verbose_name="毕业届别", related_name="graduate_classes", null=True,
                                         blank=True)
    primary_teacher = models.ForeignKey(Teacher, verbose_name="班主任", related_name="primary_classes", null=True,
                                        blank=True, on_delete=models.PROTECT)
    students = models.ManyToManyField('student', verbose_name='学生', blank=True, related_query_name='class',
                                      related_name='classes')
    major = models.ForeignKey(Major, verbose_name=Major._meta.verbose_name, null=True, blank=True, related_name='classes', related_query_name='class')
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    modify_time = models.DateTimeField("修改时间", auto_now=True)
    is_active = models.BooleanField("有效", default=True)
    courses = models.ManyToManyField("course.course", verbose_name="课程", blank=True, through="ClassCourse",
                                     related_name="school_classes")

    @cached_property
    def student_count(self):
        return self.students.count()

    student_count.short_description = '学生数'

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        from . import helper
        self.name, self.short_name, grade_name = helper.normalize_class_name(self.name)
        if not hasattr(self, 'entrance_session'):
            self.entrance_session = Session.objects.get(number=helper.grade_name_to_number(grade_name))
        if not hasattr(self, 'grade'):
            self.grade = Grade.objects.get(number=helper.cur_grade_number(grade_name))
        return super(Class, self).save(**kwargs)


class ClassCourse(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "班级课程"
        unique_together = ('clazz', 'course')

    clazz = models.ForeignKey(Class, verbose_name=Class._meta.verbose_name, on_delete=models.CASCADE,
                              related_query_name='class_course', related_name='class_courses')
    course = models.ForeignKey('course.course', verbose_name='课程', on_delete=models.CASCADE,
                               related_name='school_class_courses')
    teacher = models.ForeignKey(Teacher, verbose_name=Teacher._meta.verbose_name, null=True, blank=True,
                                on_delete=models.SET_NULL,
                                related_name='class_courses')

    def __unicode__(self):
        return "%s -> %s" % (self.clazz, self.course)


class Student(CodeMixin, models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "学生"
        ordering = ('number',)

    user = models.OneToOneField(User, verbose_name=User._meta.verbose_name, null=True, related_name="as_school_student",
                                on_delete=models.PROTECT)
    number = models.CharField("学号", max_length=32, unique=True)
    name = models.CharField("姓名", max_length=32, db_index=True)
    code = models.CharField("拼音缩写", max_length=64, db_index=True, blank=True, default="")
    grade = models.ForeignKey(Grade, verbose_name=Grade._meta.verbose_name, related_name="students",
                              on_delete=models.PROTECT)
    entrance_session = models.ForeignKey(Session, verbose_name="入学届别", related_name="entrance_students",
                                         on_delete=models.PROTECT)
    graduate_session = models.ForeignKey(Session, verbose_name="毕业届别", related_name="graduate_students", null=True,
                                         blank=True, on_delete=models.PROTECT)

    create_time = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    modify_time = models.DateTimeField("修改时间", auto_now=True)
    is_active = models.BooleanField("有效", default=True)
    is_bind = models.BooleanField("已绑", default=False)
    is_formal = models.BooleanField("正式", default=True)
    courses = models.ManyToManyField("course.course", verbose_name="课程", blank=True, related_name="school_students")

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        if not hasattr(self, 'entrance_session'):
            from . import helper
            y = helper.cur_grade_year(self.grade.number)
            self.entrance_session = Session.objects.get(number=y)
        return super(Student, self).save(**kwargs)

    @cached_property
    def class_names(self):
        return ','.join(list(self.classes.values_list('name', flat=True)))
