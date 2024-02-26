{
    "name": "Sellox Portal",
    "summary": """This module has a registration form for a user in CAW software""",
    "author": "Sellox",
    "website": "https://www.sellox.nl/",
    "category": "portal",
    "version": "14.0.0.0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "contacts"],
    # always loaded
    "data": ["data/email_template.xml", "data/ir_config_param.xml", "views/res_partner.xml", "views/templates.xml"],
    "images": ["static/description/icon.png"],
}
