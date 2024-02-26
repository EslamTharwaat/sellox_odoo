from datetime import datetime
import requests
from odoo import http
from odoo.http import request
from .const import decode_string, generate_xml_rpc_request_body, xml_to_dict, personal_data


class SelloxPortal(http.Controller):
    """Controller handling Sellox Portal functionalities."""

    @http.route("/registration_form", auth="public", website=True)
    def registration_form(self, **kw):
        # Extract person ID from request parameters
        person_id = kw.get("id", False)
        values = dict()

        # Check if person ID is provided
        if person_id not in (False, "False"):
            person_id = decode_string(person_id)

            # Retrieve personal data for the given ID
            xml_response = self.get_personal_data(person_id)
            data = xml_to_dict(xml_response)
            if not data.get("faultCode", False):

                # Parse personal data and populate values dictionary
                company_dept_function_list = [item.strip() for item in data["dept"].split(",")]
                address_list = [item.strip() for item in data["addr"].split(",")]
                name_list = [item.strip() for item in data["name"].split(",")]
                company = department = function = ""
                street = postal_code = place_name = ""
                first_name = infix = last_name = ""

                # Extract relevant information from parsed data
                if "dept" in data:
                    company_dept_function_list = [item.strip() for item in data["dept"].split(",")]
                    personal_data["company"] = company_dept_function_list[0] if len(
                        company_dept_function_list) >= 1 else ""
                    personal_data["department"] = company_dept_function_list[1] if len(
                        company_dept_function_list) >= 2 else ""
                    personal_data["function"] = ", ".join(company_dept_function_list[2:]) if len(
                        company_dept_function_list) == 3 else ""

                if "addr" in data:
                    address_list = [item.strip() for item in data["addr"].split(",")]
                    personal_data["street"] = address_list[0] if len(address_list) >= 1 else ""
                    personal_data["postal_code"] = address_list[1] if len(address_list) >= 2 else ""
                    personal_data["place_name"] = ", ".join(address_list[2:]) if len(address_list) >= 3 else ""

                if "name" in data:
                    name_list = [item.strip() for item in data["name"].split(",")]
                    personal_data["first_name"] = name_list[0] if len(name_list) >= 1 else ""
                    personal_data["infix"] = name_list[1] if len(name_list) >= 2 else ""
                    personal_data["last_name"] = ", ".join(name_list[2:]) if len(name_list) >= 3 else ""
                # Update values dictionary with extracted data
                values.update(personal_data)

                # Update values dictionary with extracted data
                values.update(
                    {
                        "name": data["name"],
                        "first_name": first_name,
                        "infix": infix,
                        "last_name": last_name,
                        "company": company,
                        "department": department,
                        "function": function,
                        "street": street,
                        "postal_code": postal_code,
                        "place_name": place_name,
                        "email": data["email"],
                        "mobile": data["mobile"],
                        "submission_date": datetime.today().date(),
                    }
                )
                # Render registration form with populated values
                return request.render("sellox_portal.portal_registration_form", values)
            else:
                # Handle error if personal data retrieval fails
                values["error"] = data["faultString"]
                return request.render("sellox_portal.portal_undefined_person", values)
        else:
            # Handle error if person ID is not provided or incorrect
            values["error"] = "Your personal id is incorrect"
            return request.render("sellox_portal.portal_undefined_person", values)

    def get_personal_data(self, person_id):
        """
        Retrieve personal data for the given person ID.

        Args:
            person_id (str): The person ID to retrieve data for.

        Returns:
            str: XML response containing personal data.

        """
        # Define the XML-RPC request body
        params = {"int": person_id}
        xml_body = generate_xml_rpc_request_body("People.get", params)

        # Retrieve Sellox configuration parameters
        ir_config_param_obj = request.env["ir.config_parameter"].sudo()
        account = ir_config_param_obj.get_param("sellox_portal.sellox_account")
        login = ir_config_param_obj.get_param("sellox_portal.sellox_login")
        password = ir_config_param_obj.get_param("sellox_portal.sellox_password")
        web_service_url = ir_config_param_obj.get_param("sellox_portal.sellox_web_service_url")

        # Create a session object to handle authentication
        session = requests.Session()
        session.auth = (f"{login}-{account}", password)

        # Make the POST request with the XML-RPC body
        response = session.post(web_service_url, data=xml_body)

        # Check if the request was successful
        if response.status_code == 200:
            return response.text
        else:
            # Return error information if request fails
            return {"error_code": response.status_code, "error_msg": response.text}

    @http.route(["/create/portal_user"], type="http", auth="public", method="post", csrf=False, website=True)
    def create_portal_user(self, **kw):
        """
        Handle creation of a portal user.

        Args:
            **kw: Keyword arguments containing user information.

        Returns:
            Rendered response indicating success or failure of user creation.

        """
        # Search for existing partner with the provided email
        partner_id = request.env["res.partner"].search([("email", "=", kw.get("email"))], limit=1)
        partner_name = f"{kw['first_name']} {kw['infix']} {kw['last_name']}"
        if not partner_id:
            # Create new partner if not found
            partner_id = (
                request.env["res.partner"]
                .sudo()
                .create(
                    {
                        "name": partner_name,
                        "email": kw["email"],
                        "street": kw["street"],
                        "zip": kw["postal_code"],
                        "street2": kw["place_name"],
                        "mobile": kw["mobile"],
                    }
                )
            )
        values = {}
        if partner_id:
            # Update partner information
            partner_id.sudo().write(
                {
                    "name": partner_name,
                    "street": kw["street"],
                    "zip": kw["postal_code"],
                    "street2": kw["place_name"],
                    "mobile": kw["mobile"],
                }
            )
            # Create portal user
            wizard_id = request.env["portal.wizard"].with_context(active_ids=[partner_id.id]).sudo().create({})
            wizard_id.user_ids[0].sudo().write({"in_portal": True})
            wizard_id.sudo().action_apply()

            return request.render("sellox_portal.portal_registration_succeeded")
