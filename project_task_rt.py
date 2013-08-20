# -*- coding: utf-8 -*-
#
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2013 Tuxservices (<http://www.tuxservices.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import logging
from lxml import etree
from lxml.builder import E

import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
import openerp.exceptions
from openerp.osv import fields, osv
from openerp.osv.orm import browse_record
from openerp.tools.translate import _
from openerp.tools import html2plaintext
import binascii
import time

_logger = logging.getLogger(__name__)

_TASK_SUBTYPE = [('task', 'Task'),('request', 'Request')]

class project_task_request(osv.Model):

    """ Project Task Request Model

        project.task.request class inherits project.task . The Task model is
        used to store the data related to the task, planning, analytic and accounting.
        The request model is now dedicated to specific request data: email handling, tracker, ...
    """

    _inherits = {
        'project.task': 'task_id',
    }
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _name = "project.task.request"
    _description = 'Request (Issue)'

    _columns = {
        'task_id': fields.many2one('project.task', required=True,
                                   string='Related Task', ondelete='cascade',
                                   help='Task-related data of the request'),
        'partner_id': fields.many2one('res.partner', 'Asked By:'),
    }

    def write(self, cr, uid, ids, values, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        
        values['subtype'] = 'request'
        values['color'] = 7
        res = super(project_task_request, self).write(cr, uid, ids, values, context=context)

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------

    def message_get_reply_to(self, cr, uid, ids, context=None):
        """ Override to get the reply_to of the parent project. """
        return [request.project_id.message_get_reply_to()[0] if request.project_id else False
                for request in self.browse(cr, uid, ids, context=context)]

    def message_get_suggested_recipients(self, cr, uid, ids, context=None):
        recipients = super(project_task_request, self).message_get_suggested_recipients(
            cr, uid, ids, context=context)
        try:
            for request in self.browse(cr, uid, ids, context=context):
                if request.partner_id:
                    self._message_add_suggested_recipient(
                        cr, uid, recipients, request, partner=request.partner_id, reason=_('Customer'))
                elif request.email_from:
                    self._message_add_suggested_recipient(
                        cr, uid, recipients, request, email=request.email_from, reason=_('Customer Email'))
        except (osv.except_osv, orm.except_orm):  # no read access rights -> just ignore suggested recipients because this imply modifying followers
            pass
        return recipients

    def message_new(self, cr, uid, msg, custom_values=None, context=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        if custom_values is None:
            custom_values = {}
        if context is None:
            context = {}
        context['state_to'] = 'draft'

        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        m  = self.pool.get('ir.model.data')
        support_categ = m.get_object(cr, uid, 'project_task_rt', 'project_category_support_r0')


        defaults = {
            'name':  msg.get('subject') or _("No Subject"),
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'partner_id': msg.get('author_id', False),
            'user_id': False,
            'categ_ids': [(6,0,[support_categ.id])],
        }

        if msg.get('priority'):
            defaults['priority'] = msg.get('priority')

        defaults.update(custom_values)
        res_id = super(project_task_request, self).message_new(
            cr, uid, msg, custom_values=defaults, context=context)
        return res_id

    def message_update(self, cr, uid, ids, msg, update_vals=None, context=None):
        """ Overrides mail_thread message_update that is called by the mailgateway
            through message_process.
            This method updates the document according to the email.
        """
        if isinstance(ids, (str, int, long)):
            ids = [ids]
        if update_vals is None:
            update_vals = {}

        # Update doc values according to the message
        if msg.get('priority'):
            update_vals['priority'] = msg.get('priority')
        # Parse 'body' to find values to update
        maps = {
            'cost': 'planned_cost',
            'revenue': 'planned_revenue',
            'probability': 'probability',
        }

        import pdb; pdb.set_trace()
        for line in msg.get('body', '').split('\n'):
            line = line.strip()
            res = tools.command_re.match(line)
            if res and maps.get(res.group(1).lower(), False):
                key = maps.get(res.group(1).lower())
                update_vals[key] = res.group(2).lower()

        return super(project_task_request, self).message_update(cr, uid, ids, 
            msg, update_vals=update_vals, context=context)

    def message_post(self, cr, uid, thread_id, body='', 
                     subject=None, type='notification', 
                     subtype=None, parent_id=False, attachments=None, 
                     context=None, content_subtype='html', **kwargs):
        
        """ Overrides mail_thread message_post so that we can set the date of last action field when
            a new message is posted on the issue.
        """
        if context is None:
            context = {}

        task_obj = self.pool.get('project.task')
        current_request = self.pool.get('project.task.request').browse(cr,uid,thread_id,context=context)[0]
        
        # update request email title to handle correct one
        new_subject = '[Support: %s] %s' %  (current_request.ref,current_request.name)

        # project_task_request model exist to handle special field value and automation for task with
        # subtype = 'request'. All chatter activity should appear on project_task model

        res = task_obj.message_post(cr, uid, [current_request.task_id.id], 
                    body=body, subject=new_subject, type=type,
                    subtype=subtype, parent_id=parent_id, 
                    attachments=attachments, context=context, 
                    content_subtype=content_subtype, **kwargs)

        if thread_id:
            self.write(cr, uid, thread_id, {'date_action_last': time.strftime(
                tools.DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)

        return res


class project(osv.Model):

    _inherit = "project.project"

    def _get_alias_models(self, cr, uid, context=None):
        return [('project.task', "Tasks"), 
                ("project.issue", "Issues"), 
                ("project.task.request", "Request (RT)")]


class task(osv.Model):

    _inherit = 'project.task'

    _columns = {
        'date_action_last': fields.datetime('Last Action', readonly=1),
        'subtype': fields.selection(_TASK_SUBTYPE, 'SubType of the task', required=True,
                        help="Fine tune type of task to handle mail_thread and automatic actions "),
    }

    _defaults = {
        'subtype': 'task',
    }