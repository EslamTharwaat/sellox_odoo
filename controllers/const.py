import base64
import xml.etree.ElementTree as ET

# Parse personal data and populate values dictionary
personal_data = {
    "company": "",
    "department": "",
    "function": "",
    "street": "",
    "postal_code": "",
    "place_name": "",
    "first_name": "",
    "infix": "",
    "last_name": ""
}


def generate_xml_rpc_request_body(method_name, params):
    method_call = ET.Element("methodCall")
    method_name_elem = ET.SubElement(method_call, "methodName")
    method_name_elem.text = method_name
    params_elem = ET.SubElement(method_call, "params")
    for key, value in params.items():
        if key == "int":
            key = "i4"
        param_elem = ET.SubElement(params_elem, "param")
        value_elem = ET.SubElement(param_elem, "value")
        value_type_elem = ET.SubElement(value_elem, key)
        value_type_elem.text = str(value)
    return ET.tostring(method_call, encoding="unicode", method="xml")


def xml_to_dict(xml_str):
    if "<?xml" in xml_str:
        xml_str = xml_str.split("?>", 1)[1]
    root = ET.fromstring(xml_str)
    xml_dict = {}
    main = root.findall(".//param")
    if len(main) > 0:
        for param in main:
            for member in param.find(".//struct").findall(".//member"):
                name_text = member.find("name").text
                member_value = member.find("value")
                value_tag = member_value[0].tag
                if value_tag != "array":
                    member_value = (
                        member_value.find(value_tag).text if member_value.find(value_tag) is not None else None
                    )
                else:
                    member_value = [
                        {value[0].tag: value.find(value[0].tag).text} for value in member_value.findall(".//value")
                    ]
                xml_dict[name_text] = member_value
    else:
        for param in root.findall(".//struct"):
            for member in param.findall(".//member"):
                name_text = member.find("name").text
                member_value = member.find("value")
                value_tag = member_value[0].tag
                if value_tag != "array":
                    member_value = (
                        member_value.find(value_tag).text if member_value.find(value_tag) is not None else None
                    )
                else:
                    member_value = [
                        {value[0].tag: value.find(value[0].tag).text} for value in member_value.findall(".//value")
                    ]
                xml_dict[name_text] = member_value
    return xml_dict


def encode_string(string):
    encoded_bytes = base64.b64encode(string.encode("utf-8"))
    encoded_string = encoded_bytes.decode("utf-8")
    return encoded_string


def decode_string(encoded_string):
    decoded_bytes = base64.b64decode(encoded_string.encode("utf-8"))
    decoded_string = decoded_bytes.decode("utf-8")
    return decoded_string
