# -*- coding:utf-8 -*-
# author : 'denishuang'
from xyz_restful.mixins import IDAndStrFieldSerializerMixin
from rest_framework.validators import UniqueTogetherValidator

from . import models, helper
from xyz_course.serializers import CourseNameSerializer
from rest_framework import serializers

import logging

log = logging.getLogger("django")


class GradeSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Grade
        fields = ('name',)


class SessionSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Session
        fields = ('name', 'number')


class MajorSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    college_name = serializers.CharField(source="college.name", read_only=True)

    class Meta:
        model = models.Major
        fields = ('name', 'code', 'college', 'college_name', 'create_time', 'courses')


class CollegeSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.College
        fields = ('name', 'code', 'create_time')


class ClassSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", label="年级" , read_only=True)
    major_name = serializers.CharField(source="major.name", read_only=True)
    entrance_session_name = serializers.CharField(source="entrance_session.name", label="入学年份", read_only=True)

    class Meta:
        model = models.Class
        fields = ('name', 'short_name', 'entrance_session', 'entrance_session_name', 'code',
                  'primary_teacher', 'grade', 'grade_name', 'students', 'major', 'major_name')
        

class ClassNameSerializer(serializers.ModelSerializer):
    class Meta(ClassSerializer.Meta):
        fields = ('name',)


class ClassListSerializer(ClassSerializer):
    class Meta(ClassSerializer.Meta):
        fields = ('id', 'name', 'student_count', 'grade', 'entrance_session', 'grade_name', 'entrance_session_name', 'major', 'major_name')


class TeacherSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    user_name = serializers.CharField(label='帐号', source="user.username", read_only=True)
    courses = CourseNameSerializer(label='课程', many=True, read_only=True, source='courses.distinct')
    classes = ClassNameSerializer(label='班级', many=True, read_only=True, source='classes.distinct')

    class Meta:
        model = models.Teacher
        fields = ('name', 'courses', 'classes', 'user_name', 'description')


class TeacherListSerializer(TeacherSerializer):
    class Meta(TeacherSerializer.Meta):
        fields = ()


class StudentSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", read_only=True)
    class_names = serializers.CharField(label='班级', read_only=True)

    class Meta:
        model = models.Student
        fields = (
            'id', 'name', 'number', 'class_names', 'classes', 'grade', 'grade_name', 'courses', 'is_active',
            'is_bind', 'is_formal'
        )


class CurrentStudentSerializer(serializers.ModelSerializer):
    school = serializers.StringRelatedField()
    clazz = serializers.StringRelatedField()
    grade = serializers.StringRelatedField()
    entrance_session = serializers.StringRelatedField()

    class Meta:
        model = models.Student
        fields = ('name', 'number', 'grade', 'entrance_session', 'clazz', 'classes', 'school', 'is_formal')


class CurrentTeacherSerializer(serializers.ModelSerializer):
    # school = SchoolSerializer()

    class Meta:
        model = models.Teacher
        fields = ('name', )


class StudentBindingSerializer(serializers.Serializer):
    mobile = serializers.CharField(label="手机号", required=True)
    number = serializers.CharField(label="学号", required=True)
    name = serializers.CharField(label="姓名", required=True)
    the_id = serializers.IntegerField(label="指定ID", required=False)

    def validate(self, data):
        assert 'request' in self.context, 'needs context[request]'
        self.request = self.context['request']
        self.cur_user = cur_user = self.request.user
        # if hasattr(cur_user, 'as_school_student'):
        #     raise serializers.ValidationError("当前帐号已绑定过,不能重复绑定")
        mobile = data['mobile']
        number = data['number']
        name = data['name']
        the_id = data.get('the_id')
        qset = models.Student.objects.filter(number=number, name=name)
        ss = []
        for s in qset:
            user = s.user
            if hasattr(user, 'as_person') and getattr(user, 'as_person').mobile == mobile:
                if not the_id or s.id == the_id:
                    ss.append(s)
        if not ss:
            raise serializers.ValidationError("相关账号不存在，可能查询信息不正确，或者还未录入系统。")
        elif len(ss) == 1:
            if ss[0].is_bind or hasattr(ss[0].user, 'as_wechat_user'):
                raise serializers.ValidationError("该帐号已绑定过，不能重复绑定。如是更换了微信，请先联系老师解绑老帐号，再重试。")
        data['students'] = ss
        return data

    def save(self):
        students = self.validated_data['students']
        if len(students) == 1:
            student = students[0]
            log.info("StudentBindingSerializer bind user %s to %s" % (self.cur_user, student))
            helper.bind(student, self.cur_user)
            from django.contrib.auth import login
            login(self.request, student.user, backend='binding')
        return [unicode(s) for s in students]


class ClassCourseSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    clazz_name = serializers.CharField(source="clazz.name", label="班名", read_only=True)
    course_name = serializers.CharField(source="course.name", label="课名", read_only=True)
    teacher_name = serializers.CharField(source="teacher.name", label="老师", read_only=True)

    class Meta:
        model = models.ClassCourse
        fields = ('clazz', 'course', 'teacher', 'clazz_name', 'course_name', 'teacher_name')
        validators = [
            UniqueTogetherValidator(
                queryset=models.ClassCourse.objects.all(),
                fields=['clazz', 'course'],
                message='相同记录已存在, 请不要重复创建.'
            )
        ]
