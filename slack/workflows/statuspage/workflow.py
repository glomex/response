import statuspageio

import logging
logger = logging.getLogger(name="statuspage init")

from .action_handler import *
from .incident_command import *
from .dialog_handler import *
from .constants import *

from .connections import set_status_page_conn

from slack.models import Workflow
from slack.decorators import incident_command, remove_incident_command
from slack.decorators import action_handler, remove_action_handler, ActionContext
from slack.decorators import dialog_handler, remove_dialog_handler
from slack.decorators.workflow import register_workflow, WorkflowClass


@register_workflow('statuspage')
class Statuspage(WorkflowClass):
    configuration_values = ['STATUSPAGEIO_API_KEY', 'STATUSPAGEIO_PAGE_ID']

    def enable(self, workflow: Workflow):
        params = dict((x.name, x.value) for x in workflow.parameters.all())

        required = ['STATUSPAGEIO_API_KEY', 'STATUSPAGEIO_PAGE_ID']
        if not all([ params[x] for x in params.keys() & required]):
            logger.warn("Not all required parameters are set for statuspage workflow.")
            return

        set_status_page_conn(statuspageio.Client(api_key=params['STATUSPAGEIO_API_KEY'],
                                          page_id=params['STATUSPAGEIO_PAGE_ID']))

        incident_command(STATUS_PAGE_COMMANDS, handle_statuspage, helptext='Update the statuspage for this incident')
        action_handler(OPEN_STATUS_PAGE_DIALOG, handle_open_status_page_dialog)
        dialog_handler(STATUS_PAGE_UPDATE, handle_status_page_update)

    def disable(self, workflow: Workflow):
        set_status_page_conn(None)
        remove_incident_command(STATUS_PAGE_COMMANDS)
        remove_action_handler(OPEN_STATUS_PAGE_DIALOG)
        remove_dialog_handler(STATUS_PAGE_UPDATE)
