# -*- coding:utf-8 -*-
from __future__ import unicode_literals
SCHOOL_TYPE_KINDERGARTEN = 0
SCHOOL_TYPE_PRIMARY = 1
SCHOOL_TYPE_MIDDLE = 2
SCHOOL_TYPE_UNIVERSITY = 3
SCHOOL_TYPE_VOCATIONAL = 4
CHOICES_SCHOOL_TYPE = (
    (SCHOOL_TYPE_KINDERGARTEN, '幼儿园'),
    (SCHOOL_TYPE_PRIMARY, '小学'),
    (SCHOOL_TYPE_MIDDLE, '中学'),
    (SCHOOL_TYPE_UNIVERSITY, '大学'),
    (SCHOOL_TYPE_VOCATIONAL, '职校')
)

CHOICES_GRADE_KINDERGARTEN = (
    (1, "小班"),
    (2, "中班"),
    (3, "大班"),
)

CHOICES_GRADE_PRIMARY = (
    (1, "一年级"),
    (2, "二年级"),
    (3, "三年级"),
    (4, "四年级"),
    (5, "五年级"),
    (6, "六年级"),
)

CHOICES_GRADE_PRIMARY9 = CHOICES_GRADE_PRIMARY + (
    (7, "七年级"),
    (8, "八年级"),
    (9, "九年级"),
)

CHOICES_GRADE_MIDDLE = (
    (1, "初一"),
    (2, "初二"),
    (3, "初三"),
    (11, "高一"),
    (12, "高二"),
    (13, "高三"),
)

CHOICES_GRADE_UNIVERSITY = CHOICES_GRADE_VOCATIONAL = (
    (1, "大一"),
    (2, "大二"),
    (3, "大三"),
    (4, "大四"),
    (11, "硕一"),
    (12, "硕二"),
    (13, "硕三"),
)


MAP_SCHOOL_TYPE_GRADES = {
    SCHOOL_TYPE_KINDERGARTEN: CHOICES_GRADE_KINDERGARTEN,
    SCHOOL_TYPE_PRIMARY: CHOICES_GRADE_PRIMARY,
    SCHOOL_TYPE_MIDDLE: CHOICES_GRADE_MIDDLE,
    SCHOOL_TYPE_UNIVERSITY: CHOICES_GRADE_UNIVERSITY,
    SCHOOL_TYPE_VOCATIONAL: CHOICES_GRADE_VOCATIONAL,
}
