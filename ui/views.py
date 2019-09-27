from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, Http404
from django.template.defaulttags import register
from django.core.paginator import Paginator

from core.models import Incident
from slack.models import PinnedMessage, UserStats


@register.filter
def get_range(value):
    return range(value)


def incident_doc(request: HttpRequest, incident_id: str):

    try:
        incident = Incident.objects.get(pk=incident_id)
    except Incident.DoesNotExist:
        raise Http404("Incident does not exist")

    events = PinnedMessage.objects.filter(incident=incident).order_by('timestamp')
    user_stats = UserStats.objects.filter(incident=incident).order_by('-message_count')[:5]

    return render(request, template_name='incident_doc.html', context={
        "incident": incident,
        "events": events,
        "user_stats": user_stats,
    })


def incident_list(request: HttpRequest):
    incident = Incident.objects.all().order_by('-start_time')
    paginator = Paginator(incident, 6)
    page = request.GET.get('page')
    incident = paginator.get_page(page)

    return render(request, template_name='incident_list.html', context={
        "incidents": incident,
    })
