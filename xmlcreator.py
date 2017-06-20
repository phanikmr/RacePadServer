import xml.etree.cElementTree as xml


def create_empty_xml_profile(root, sub_element_list):
    tree_root = xml.Element(root)
    for i in range(len(sub_element_list)):
        tag = xml.SubElement(tree_root, sub_element_list[i].strip())
        tag.text = ""
    tree = xml.ElementTree(tree_root)
    tree.write("data/temp_profile.xml")


def edit_xml_profile(sub_element, sub_element_value):
    tree = xml.ElementTree(file="data/temp_profile.xml")
    root = tree.getroot()
    for tag in root.iter(sub_element):
        tag.text = str(sub_element_value)
    tree = xml.ElementTree(root)
    tree.write("data/temp_profile.xml")


def parse_xml_profile(filename, tag_name):
    tree = xml.ElementTree(file=filename)
    root = tree.getroot()
    for tag in root:
        if tag.tag == tag_name:
            return tag.text
    return None


if __name__ == "__main__":
    create_empty_xml_profile("student", ["name", "age", "class"])
    edit_xml_profile("name", "PhaniKumar")
