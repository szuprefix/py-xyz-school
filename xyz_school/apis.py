# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from xyz_auth.authentications import add_token_for_user
from xyz_restful.mixins import BatchActionMixin
from xyz_util.statutils import do_rest_stat_action

from . import models, serializers, importers, helper, stats
from rest_framework import viewsets, decorators, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from xyz_restful.decorators import register

__author__ = 'denishuang'


@register()
class TeacherViewSet(viewsets.ModelViewSet):
    queryset = models.Teacher.objects.all()
    serializer_class = serializers.TeacherSerializer
    filter_fields = {
        'id': ['in', 'exact'],
        'name': ['exact'],
        'user': ['exact']
    }
    search_fields = ('name', 'code')
    ordering_fields = ('name', 'code')

    @decorators.list_route(['get'])
    def stat(self, request):
        return do_rest_stat_action(self, stats.stats_teacher)


@register()
class GradeViewSet(viewsets.ModelViewSet):
    queryset = models.Grade.objects.all()
    serializer_class = serializers.GradeSerializer


@register()
class SessionViewSet(viewsets.ModelViewSet):
    queryset = models.Session.objects.all()
    serializer_class = serializers.SessionSerializer
    search_fields = ('name', 'number')
    filter_fields = {'id': ['in', 'exact']}


@register()
class ClassViewSet(viewsets.ModelViewSet):
    queryset = models.Class.objects.all()
    serializer_class = serializers.ClassSerializer
    search_fields = ('name', 'code')
    filter_fields = {
        'id': ['in', 'exact'],
        'name': ['exact', 'endswith', 'in'],
        'code': ['in', 'exact'],
        'entrance_session': ['in', 'exact'],
        'grade': ['in', 'exact']
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.ClassListSerializer
        return super(ClassViewSet, self).get_serializer_class()

    @decorators.list_route(['get'])
    def similar(self, request):
        q = request.query_params.get('q')
        import Levenshtein
        from django.db.models import F
        from xyz_util.modelutils import CharCorrelation
        qset = self.filter_queryset(self.get_queryset()).values('name', a=CharCorrelation([F('name'), q])).filter(
            a__gt=0).order_by('-a').values_list('name', 'a')[:10]
        aa = [(Levenshtein.ratio(n, q), c, n) for n, c in qset]
        aa.sort(reverse=True)
        ss = [c for a, b, c in aa if a > 0.5]
        return Response({'similar': ss})

    @decorators.list_route(['get'])
    def stat(self, request):
        return do_rest_stat_action(self, stats.stats_class)

    @decorators.list_route(['get'])
    def sumary(self, request):
        qset = self.filter_queryset(self.get_queryset())
        dl = []
        dl.append('班级,学生数,课程数,课程'.split(','))
        for c in qset:
            dl.append([c.name, c.students.count(), c.courses.count(),
                       ",".join(list(c.courses.values_list('name', flat=True)))])
        return Response({'data': dl})

@register()
class MajorViewSet(viewsets.ModelViewSet):
    queryset = models.Major.objects.all()
    serializer_class = serializers.MajorSerializer
    search_fields = ('name', 'code')
    filter_fields = {
        'code': ['exact'],
        'name': ['exact', 'in'],
        'id': ['in', 'exact'],
    }


@register()
class CollegeViewSet(viewsets.ModelViewSet):
    queryset = models.College.objects.all()
    serializer_class = serializers.CollegeSerializer
    search_fields = ('name', 'code')
    filter_fields = ('code', 'name',)


@register()
class ClassCourseViewSet(viewsets.ModelViewSet):
    queryset = models.ClassCourse.objects.all()
    serializer_class = serializers.ClassCourseSerializer
    search_fields = ('clazz__name', 'course__name')
    filter_fields = {
        'id': ['in', 'exact'],
        'clazz': ['exact'],
        'course': ['exact'],
        'teacher': ['exact']
    }


@register()
class StudentViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.Student.objects.all()
    serializer_class = serializers.StudentSerializer
    search_fields = ('name', 'number', 'code')
    filter_fields = {
        'id': ['in', 'exact'],
        'grade': ['exact'],
        'class': ['exact', 'in'],
        'number': ['exact', 'in'],
        'is_active': ['exact'],
        'is_bind': ['exact'],
        'is_formal': ['exact'],
        'class__id': ['exact', 'in'],
        'user': ['exact']
    }
    ordering_fields = ('name', 'number', 'create_time', 'grade', 'clazz')

    def get_permissions(self):
        if self.action in ['binding', 'trial_application']:
            return [IsAuthenticated()]
        return super(StudentViewSet, self).get_permissions()

    @decorators.list_route(['post'])
    def pre_import(self, request):
        importer = importers.StudentImporter()
        data = importer.clean(importer.get_excel_data(request.data['file']))
        return Response(data)

    @decorators.list_route(['post'])
    def post_import(self, request):
        importer = importers.StudentImporter()
        student, created = importer.import_one(request.data)
        return Response(self.get_serializer(instance=student).data,
                        status=created and status.HTTP_201_CREATED or status.HTTP_200_OK)

    @decorators.list_route(['POST'])
    def batch_active(self, request):
        return self.do_batch_action('is_active', True)

    @decorators.list_route(['POST'], permission_classes=[IsAuthenticated])
    def trial_application(self, request):
        helper.apply_to_be_student(request.user, request.data)
        return Response({'detail': 'ok'})

    @decorators.list_route(['post'], permission_classes=[IsAuthenticated])
    def binding(self, request):
        serializer = serializers.StudentBindingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            schools = serializer.save()
            data = serializer.data
            data['schools'] = schools
            add_token_for_user(data, request.user)
            return Response(data)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @decorators.list_route(['POST'])
    def batch_unbind(self, request):
        return self.do_batch_action(helper.unbind)

    @decorators.list_route(['POST'])
    def batch_reset_password(self, request):
        return self.do_batch_action(helper.reset_password)

    @decorators.detail_route(['post'])
    def unbind(self, request):
        helper.unbind(self.get_object())
        return Response({'info': 'success'})

    @decorators.list_route(['get'])
    def stat(self, request):
        return do_rest_stat_action(self, stats.stats_student)
