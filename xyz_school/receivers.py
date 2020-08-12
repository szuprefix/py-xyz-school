# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from django.dispatch import receiver
from django.db.models.signals import post_save
from xyz_auth.signals import to_get_user_profile
from xyz_saas.signals import to_get_party_settings
from xyz_verify.models import Verify
from . import models, helper, serializers, choices
from django.conf import settings
from xyz_util.datautils import access
import logging

log = logging.getLogger("django")
# from xyz_tenant.models import App


# @receiver(post_save, sender=App)
# def init_grade(sender, **kwargs):
#     app = kwargs['instance']
#     if app.name != 'school':
#         return
#     from tenant_schemas.utils import tenant_context
#     with tenant_context(app.tenant):
#         try:
#             if models.Grade.objects.count() == 0:
#                 helper.gen_default_grades(app.settings.get('type', choices.SCHOOL_TYPE_UNIVERSITY))
#         except Exception, e:
#             log.error("init_grade error: %s" % e)


@receiver(post_save, sender=models.Grade)
def init_session(sender, **kwargs):
    try:
        grade = kwargs['instance']
        helper.gen_default_session(grade.number - 1)
    except Exception, e:
        log.error("init_session error: %s" % e)


# @receiver(post_save, sender=models.Student)
# def add_student_to_clazz_names(sender, **kwargs):
#     try:
#         student = kwargs['instance']
#         clazz = student.clazz
#         ns = clazz.student_names
#         # print student.name, ns
#         if student.name not in ns:
#             clazz.student_names.append(student.name)
#             clazz.save()
#     except Exception, e:
#         import traceback
#         log.error("add_student_to_class_names error: %s, %s", e, traceback.format_exc())
#

# @receiver(post_save, sender=Worker)
# def init_student(sender, **kwargs):
#     # try:
#     worker = kwargs['instance']
#     # print worker
#     if worker.position != '学生':
#         return
#     tasks.init_student.delay(worker.id)
#     # except Exception, e:
#     #     log.error("init_student error: %s" % e)

@receiver(to_get_user_profile)
def get_school_profile(sender, **kwargs):
    user = kwargs['user']
    if hasattr(user, 'as_school_student'):
        return serializers.CurrentStudentSerializer(user.as_school_student, context=dict(request=kwargs['request']))
    if hasattr(user, 'as_school_teacher'):
        return serializers.CurrentTeacherSerializer(user.as_school_teacher, context=dict(request=kwargs['request']))


@receiver(to_get_party_settings)
def get_school_settings(sender, **kwargs):
    return {'school': {'student': {'unregistered': access(settings, 'SCHOOL.STUDENT.UNREGISTERED')}}}

@receiver(post_save, sender=Verify)
def create_student_after_verify(sender, **kwargs):
    created = kwargs.get('created')
    if created:
        return
    helper.create_student_after_verify(kwargs.get('instance'))

def create_student_for_wechat_user(sender, **kwargs):
    wuser = kwargs['instance']
    helper.create_student_for_wechat_user(wuser)


def bind_create_student_for_wechat_user_receiver():
    b = access(settings, 'SCHOOL.STUDENT.UNREGISTERED')
    if not b or b.lower() != 'create_from_wechat':
        return
    from xyz_wechat.models import User
    from django.db.models.signals import post_save
    print 'bind_create_student_for_wechat_user_receiver'
    post_save.connect(create_student_for_wechat_user, sender=User)


bind_create_student_for_wechat_user_receiver()
