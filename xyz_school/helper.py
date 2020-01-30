# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.db.models import NOT_PROVIDED, ForeignKey
from xyz_util import dateutils, datautils
from . import choices, models
import re


def gen_default_grades(school):
    gs = choices.MAP_SCHOOL_TYPE_GRADES.get(school.type)
    if not gs:
        return
    for number, name in gs:
        school.grades.create(name=name, number=number)


def gen_default_session(school, offset=0):
    today = dateutils.format_the_date()
    year = today.month >= 8 and today.year or today.year - 1
    year -= offset
    return school.sessions.get_or_create(
        number=year,
        defaults=dict(
            name="%s届" % year,
            begin_date="%s-09-01" % year,
            end_date="%s-07-01" % (year + 1))
    )


RE_CLASS_GRADE_NAME = re.compile(r"^(\d{4}|\d{2})[级届]*")


def normalize_class_name(class_name, grade=None):
    """
    In [18]: a=helper.normalize_class_name(u"2000级计算机A班"); print a[0],a[1],a[2]
    2000级计算机A班 计算机A班 2000级

    In [19]: a=helper.normalize_class_name(u"92级计算机A班"); print a[0],a[1],a[2]
    1992级计算机A班 计算机A班 1992级

    In [20]: a=helper.normalize_class_name(u"28级计算机A班"); print a[0],a[1],a[2]
    2028级计算机A班 计算机A班 2028级

    In [21]: a=helper.normalize_class_name(u"28级计算机A班",u"92级"); print a[0],a[1],a[2]
    92级计算机A班 计算机A班 92级
    """

    m = RE_CLASS_GRADE_NAME.search(class_name)
    if m:
        g = m.group(0)
        class_name = class_name[m.pos + len(g):]
        if not class_name:
            class_name = g[2:]
            g = g[:2]
        g = "%s级" % grade_name_to_number(g)
        if not grade:
            grade = g
        grade = normalize_grade_name(grade, g)
    else:
        grade = normalize_grade_name(grade)
    if not class_name.endswith("班"):
        class_name = "%s班" % class_name
    return "%s%s" % (grade, class_name), class_name, grade


def class_name_to_number(class_name):
    RE_CLASS_NUMBER = re.compile(r"([0-9一二三四五六七八九]+)班")
    m = RE_CLASS_NUMBER.search(class_name)
    if m:
        return datautils.cn2digits(m.groups()[0])


def normalize_grade_name(grade, default=None):
    """
    In [56]: print helper.normalize_grade_name(u"98届")
    1998级

    In [57]: print helper.normalize_grade_name(u"00届")
    2000级

    In [58]: print helper.normalize_grade_name(u"2010届")
    2010级

    In [60]: print helper.normalize_grade_name(u"2099届",u"2019级")
    2019级

    """

    if not grade:
        return default
    no = short_year_to_full_year(grade_name_to_number(grade))
    from datetime import datetime
    if no > datetime.now().year:
        grade = default
    else:
        grade = "%d级" % no
    if grade[-1] != "级":
        grade += "级"
    return grade


RE_MAJOR = re.compile(r"([^\(\)]*)(\(([^\(\)]*)\)|)")


def normalize_major_name(major):
    major = major.replace(" ", "").replace("（", "(").replace("）", ")")
    m = RE_MAJOR.search(major)
    if m:
        return m.group(1), m.group(3)
    return major, None


RE_GRADE = re.compile(r"(\d+)[级届]*")
RE_GRADE2 = re.compile(r"(\d+)[年级]*")


def short_year_to_full_year(no):
    """
    In [33]: helper.short_year_to_full_year(49)
    Out[33]: 2049

    In [34]: helper.short_year_to_full_year(50)
    Out[34]: 1950

    In [35]: helper.short_year_to_full_year(99)
    Out[35]: 1999

    In [36]: helper.short_year_to_full_year(100)
    Out[36]: 100

    In [37]: helper.short_year_to_full_year(1)
    Out[37]: 2001

    In [38]: helper.short_year_to_full_year(2010)
    Out[38]: 2010
    """
    assert no >= 0, "不能小于0"
    return no < 50 and no + 2000 or no < 100 and no + 1900 or no


def grade_name_to_number(grade_name):
    """
    In [43]: helper.grade_name_to_number(u"98届")
    Out[43]: 1998

    In [44]: helper.grade_name_to_number(u"98级")
    Out[44]: 1998

    In [45]: helper.grade_name_to_number(u"12级")
    Out[45]: 2012

    In [46]: helper.grade_name_to_number(u"23级")
    Out[46]: 2023

    In [47]: helper.grade_name_to_number(u"1923级")
    Out[47]: 1923
    """
    m = RE_GRADE.search(grade_name)
    if m:
        sno = m.group(1)
        return short_year_to_full_year(int(sno))


def cur_grade_number(grade_name, today=None):
    """
     when today is 2016.9.10

     cur_grade_number("14级")
     3
     cur_grade_number("2015级")
     2
     cur_grade_number("2016级")
     1
     cur_grade_number("98级")
     19
     cur_grade_number("17级")
     0
     cur_grade_number("18级")
     -1
    """
    gno = grade_name_to_number(grade_name)
    if not gno:
        return
    today = today or datetime.date.today()
    num = today.year - gno
    if today.month >= 8:
        num += 1
    return num


def cur_grade_year(grade_num, today=None):
    today = today or datetime.date.today()
    year = today.year - grade_num
    if today.month >= 8:
        year += 1
    return year


def cur_grade_name(grade_num, today=None):
    return "%s级" % cur_grade_year(grade_num, today)


def get_cur_term(corp):
    today = dateutils.format_the_date()
    year = today.month >= 8 and today.year or today.year - 1
    month = today.month
    day = today.day
    part = (month * 100 + day < 215 or month >= 8) and 1 or 2
    name = "%s-%s学年第%s学期" % (year, year + 1, part == 1 and "一" or "二")
    start_date = datetime.date(today.year, part == 1 and 9 or 3, 1)
    term, created = corp.school_terms.get_or_create(year=year,
                                                    part=part,
                                                    defaults=dict(name=name,
                                                                  start_date=start_date))
    return term


def init_student(user, profile):

    def get_field_value_from_profile(profile, fs):
        r = {}
        for f in fs:
            if isinstance(f, (ForeignKey)):
                fo, created = f.related_model.objects.get_or_create(name=profile.get(f.verbose_name))
                r[f.name] = fo
            else:
                r[f.name] = profile.get(f.verbose_name, f.default != NOT_PROVIDED and f.default or None)
        return r

    fns = "number,name".split(",")
    fs = [f for f in models.Student._meta.local_fields if f.name in fns]
    ps = get_field_value_from_profile(profile, fs)

    grade_name = profile.get('年级')
    grade_number = cur_grade_number(grade_name)
    grade, created = models.Grade.get_or_create(number=grade_number)
    ps['grade'] = grade

    session_number = grade_name_to_number(grade_name)
    session, created = models.Session.get_or_create(number=session_number)
    ps['entrance_session'] = session

    class_names = profile.get('班级')
    classes = []
    for cn in class_names.split(','):
        clazz, created = models.Class.get_or_create(
            name=cn,
            defaults=dict(
                entrance_session=session,
                grade=grade
            )
        )
        classes.append(clazz)
    ps['clazz'] = classes and classes[0] or None
    ps['user'] = user

    student, created = school.students.update_or_create(
        number=worker.number,
        defaults=ps)
    student.classes = classes
    major_name = profile.get("专业")
    if major_name:
        student.majors = school.majors.filter(name__in=major_name.split(","))
    return student, created


def bind(student, old_user):
    user = student.user
    from xyz_auth.signals import to_bind_user
    from django.db import transaction
    with transaction.atomic():
        to_bind_user.send(student._meta.model, old_user=old_user, new_user=user)
        user.set_password(student.number)
        user.save()
        student.is_bind = True
        student.save()
    from xyz_common.signals import to_add_event
    to_add_event.send_robust(sender=student._meta.model, instance=student, name='bind')


def unbind(student):
    user = student.user
    from django.db import transaction
    with transaction.atomic():
        if hasattr(user, 'as_wechat_user'):
            user.as_wechat_user.delete()
        user.set_unusable_password()
        user.save()
        student.is_bind = False
        student.save()

