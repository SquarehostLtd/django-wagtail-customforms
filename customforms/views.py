from __future__ import absolute_import, unicode_literals

import csv
import datetime
import json

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import smart_str
from django.utils.translation import ungettext

from wagtail.admin import messages
from wagtail.admin.forms import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.core import hooks
from wagtail.core.models import Page, Collection
from wagtail.contrib.forms.forms import SelectDateForm
from wagtail.search import index as search_index
from wagtail.utils.pagination import paginate

from .forms import get_form_form
from .models import Form
from .permissions import permission_policy

def index(request):
    # form_pages = get_forms_for_user(request.user)

    forms = Form.objects.all()

    paginator, form_pages = paginate(request, forms)

    return render(request, 'wagtailforms/index.html', {
        'form_pages': forms,
    })


def delete_submissions(request, page_id):
    # if not get_forms_for_user(request.user).filter(id=page_id).exists():
    #     raise PermissionDenied

    # page = get_object_or_404(Page, id=page_id).specific
    page = get_object_or_404(Form, id=page_id)

    # Get submissions
    submission_ids = request.GET.getlist('selected-submissions')
    submissions = page.get_submission_class()._default_manager.filter(id__in=submission_ids)

    if request.method == 'POST':
        count = submissions.count()
        submissions.delete()

        messages.success(
            request,
            ungettext(
                "One submission has been deleted.",
                "%(count)d submissions have been deleted.",
                count
            ) % {
                'count': count,
            }
        )

        return redirect('wagtailforms:list_submissions', page_id)

    return render(request, 'wagtailforms/confirm_delete.html', {
        'page': page,
        'submissions': submissions,
    })


def list_submissions(request, page_id):
    # if not get_forms_for_user(request.user).filter(id=page_id).exists():
    #     raise PermissionDenied

    form_page = get_object_or_404(Form, id=page_id)#.specific
    form_submission_class = form_page.get_submission_class()

    data_fields = form_page.get_data_fields()

    submissions = form_submission_class.objects.filter(form=form_page).order_by('submit_time')
    data_headings = [label for name, label in data_fields]

    select_date_form = SelectDateForm(request.GET)
    if select_date_form.is_valid():
        date_from = select_date_form.cleaned_data.get('date_from')
        date_to = select_date_form.cleaned_data.get('date_to')
        # careful: date_to should be increased by 1 day since the submit_time
        # is a time so it will always be greater
        if date_to:
            date_to += datetime.timedelta(days=1)
        if date_from and date_to:
            submissions = submissions.filter(submit_time__range=[date_from, date_to])
        elif date_from and not date_to:
            submissions = submissions.filter(submit_time__gte=date_from)
        elif not date_from and date_to:
            submissions = submissions.filter(submit_time__lte=date_to)

    if request.GET.get('action') == 'CSV':
        # return a CSV instead
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename=export.csv'

        # Prevents UnicodeEncodeError for labels with non-ansi symbols
        data_headings = [smart_str(label) for label in data_headings]

        writer = csv.writer(response)
        writer.writerow(data_headings)
        for s in submissions:
            data_row = []
            form_data = s.get_data()
            for name, label in data_fields:
                val = form_data.get(name)
                if isinstance(val, list):
                    val = ', '.join(val)
                data_row.append(smart_str(val))
            writer.writerow(data_row)
        return response

    paginator, submissions = paginate(request, submissions)

    data_rows = []
    for s in submissions:
        form_data = s.get_data()
        data_row = []
        for name, label in data_fields:
            val = form_data.get(name)
            if isinstance(val, list):
                val = ', '.join(val)
            data_row.append(val)
        data_rows.append({
            "model_id": s.id,
            "fields": data_row
        })

    return render(request, 'wagtailforms/index_submissions.html', {
        'form_page': form_page,
        'select_date_form': select_date_form,
        'submissions': submissions,
        'data_headings': data_headings,
        'data_rows': data_rows
    })


def chooser(request):
    if permission_policy.user_has_permission(request.user, 'add'):
        FormForm = get_form_form(Form)
        uploadform = FormForm(user=request.user)
    else:
        uploadform = None

    forms = Form.objects.all()

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_form_chooser_queryset'):
        forms = hook(documents, request)

    q = None
    if 'q' in request.GET or 'p' in request.GET or 'collection_id' in request.GET:

        collection_id = request.GET.get('collection_id')
        if collection_id:
            forms = forms.filter(collection=collection_id)

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            forms = forms.search(q)
            is_searching = True
        else:
            forms = forms.order_by('-created_at')
            is_searching = False

        # Pagination
        paginator, forms = paginate(request, forms, per_page=10)

        return render(request, "customforms/chooser/results.html", {
            'forms': forms,
            'query_string': q,
            'is_searching': is_searching,
        })
    else:
        searchform = SearchForm()

        collections = Collection.objects.all()
        if len(collections) < 2:
            collections = None

        forms = forms.order_by('-created_at')
        paginator, forms = paginate(request, forms, per_page=10)

        return render_modal_workflow(request, 'customforms/chooser/chooser.html', 'customforms/chooser/chooser.js', {
            'forms': forms,
            'uploadform': uploadform,
            'searchform': searchform,
            'collections': collections,
            'is_searching': False,
        })


def get_form_json(form):
    edit_link = '/admin/customforms/form/edit/%s/' % form.pk
    return json.dumps({
        'id': form.id,
        'title': form.title,
        'edit_link': edit_link#reverse('wagtaildocs:edit', args=(form.id,)),
    })


def form_chosen(request, form_id):
    form = get_object_or_404(Form, id=form_id)
    return render_modal_workflow(
        request, None, 'customforms/chooser/form_chosen.js',
        {'form_json': get_form_json(form)}
    )


# @permission_checker.require('add')
def chooser_upload(request):
    FormForm = get_form_form(Form)

    if request.method == 'POST':
        form = Form(uploaded_by_user=request.user)
        form_form = FormForm(request.POST, request.FILES, instance=form, user=request.user)

        if form_form.is_valid():
            form_form.save()

            # Reindex the document to make sure all tags are indexed
            search_index.insert_or_update_object(form)

            return render_modal_workflow(
                request, None, 'customforms/chooser/form_chosen.js',
                {'form_json': get_form_json(form)}
            )
    else:
        form_form = FormForm(user=request.user)

    forms = Form.objects.order_by('title')

    return render_modal_workflow(
        request, 'customforms/chooser/chooser.html', 'customforms/chooser/chooser.js',
        {'forms': forms, 'uploadform': form}
    )


def submit(request, form_id):
    from django.contrib import messages
    try:
        value = Form.objects.get(pk=form_id)
    except:
        pass
    if request.method == 'POST':
        form = value.get_form(request.POST, request.FILES, page=value, user=request.user)
        if form.is_valid():
            value.process_form_submission(form)
            messages.add_message(request, messages.SUCCESS, 'Thank you for submitting the form.')
        else:
            messages.add_message(request, messages.ERROR, 'There was an error on the form, please correct it.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
