import logging

from odoo import _, models
from odoo.exceptions import UserError

from ..controllers.const import encode_string


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_send_registration_form(self):
        """send registration form email to user"""
        self.ensure_one()
        if not self.email:
            raise UserError(_("You must have an email address in this contact to send emails."))

        # determine subject and body in the portal user's language
        template = self.env.ref("sellox_portal.mail_template_sellox_registration_form")

        if template:
            template.with_context(lang=self.lang, id=f"id={encode_string(str(self.ref))}").send_mail(
                self.id, force_send=True
            )
        else:
            _logger.warning("No email template found for sending email to the portal user")

        return True
