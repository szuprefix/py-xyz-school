# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from xyz_util.importutils import BaseImporter, WARNING_KEY
from .validators import *
from xyz_util import datautils
from . import models

__author__ = 'denishuang'


def format_class_grade(d):
    from .helper import normalize_class_name
    v = d.get(field_class.name)
    g = d.get(field_grade.name)
    if v and g:
        d[field_class.name] = ','.join([normalize_class_name(a, g)[0] for a in v.split(',')])


class ClazzImporter(BaseImporter):
    fields = [
        field_class,
        field_grade,
        field_session
    ]
    min_fields_count = 2
    key_field = field_class
    required_fields = [field_class, field_grade]


class StudentImporter(BaseImporter):
    fields = [
        field_han_name,
        field_student_number,
        MobileField(synonyms=["学生手机号"]),
        field_weixinid,
        field_email,
        field_qq,
        field_college,
        field_major,
        field_grade,
        field_class,
        field_idcard,
        field_instructor
    ]
    min_fields_count = 3
    key_field = field_student_number
    required_fields = [field_student_number, field_mobile]
    extra_cleans = [format_class_grade]

    def __init__(self):
        # self.root_department = '学生'
        return super(StudentImporter, self).__init__()

    def import_one(self, d):
        from django.contrib.auth.models import User
        snumber = d.get(field_student_number.name)

        name = d.get(field_han_name.name)
        user, created = User.objects.update_or_create(
            username='%s@student' % snumber,
            defaults=dict(first_name=name)
        )
        from .helper import init_student
        student, created = init_student(user, d)
        from xyz_auth.signals import to_save_user_profile
        to_save_user_profile.send(self, user=user, profile=d)
        return student, created

    def clean_item(self, obj):
        res = super(StudentImporter, self).clean_item(obj)
        fn = field_student_number.name
        num = res.get(fn)
        e = models.Student.objects.filter(number=num).exists()
        wks = res.get(WARNING_KEY)
        if e:
            errs = wks.setdefault(fn, [])
            errs.append("已存在")
        return res


def bind_worker_number_to_pinyin_name(d):
    worker_number, e = d.get("工号")
    if not worker_number:
        name, e2 = d.get("姓名")
        from unidecode import unidecode
        d["工号"] = (unidecode(name).replace(" ", ""), [])
        d.warnings.append("自动根据姓名生成工号")


class TeacherImporter(BaseImporter):
    fields = [
        field_han_name,
        field_worker_number,
        field_mobile,
        field_weixinid,
        field_email,
        field_department,
        field_position,
        field_is_instructor,
        field_is_counsellor,
    ]
    min_fields_count = 3

    extra_cleans = [bind_worker_number_to_pinyin_name]

    def import_one(self, api, d):
        wx_userid = d.get(field_worker_number.name)
        department_path = "%s" % d.get(field_department.name, "未指定部门")
        department = api.corp.departments.filter(name=department_path).first()
        if not department:
            department, created = api.get_or_create_department_by_path(department_path)
        worker, created = api.corp.workers.update_or_create(
            wx_userid=wx_userid,
            defaults=dict(
                mobile=d.get(field_mobile.name),
                position=d.get(field_position.name, "教师"),
                gender={"男": 1, "女": 2}.get(d.get("性别"), 0),
                name=d.get(field_han_name.name),
                email=d.get(field_email.name),
                weixinid=d.get(field_weixinid.name)
            )
        )
        worker.update_extattr(
            datautils.exclude_dict_keys(
                d,
                field_weixinid.name, field_email.name, field_mobile.name,
                field_department.name, field_position.name, field_han_name.name,
                "性别"))
        worker.departments = [department]
        return worker, created

    def extra_action(self, api, worker, created):
        ur = api.upload_worker(worker)
        return ur.get("errcode") == 0 or ur
