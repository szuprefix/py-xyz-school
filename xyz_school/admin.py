# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models, helper


@admin.register(models.Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("name", 'code')
    search_fields = ("name",)


@admin.register(models.Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ("name", 'code')
    search_fields = ("name",)


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("name",)
    raw_id_fields = ("entrance_session", "graduate_session", "primary_teacher", "grade")
    search_fields = ("name",)


def unbind_student(modeladmin, request, queryset):
    for student in queryset.all():
        helper.unbind(student)


unbind_student.short_description = u"解除绑定"


@admin.register(models.Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", 'number', 'class_names', 'create_time')
    raw_id_fields = ("entrance_session", "graduate_session", "grade", 'user')
    search_fields = ('name', 'number')
    actions = [unbind_student]


@admin.register(models.Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name",)
    raw_id_fields = ('user',)
    search_fields = ('name',)

@admin.register(models.ClassCourse)
class ClassCourseAdmin(admin.ModelAdmin):
    list_display = ("clazz", "course", "teacher")
    list_select_related = ("clazz", "course", "teacher")
    search_fields = ('clazz__name', "course__name")
    raw_id_fields = ('clazz', 'course', 'teacher')
