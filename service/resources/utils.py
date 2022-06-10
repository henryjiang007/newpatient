import os
import requests
import time
import pdfrw

# PDF Format Keys
ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_FIELD_TYPE = '/FT'
ANNOT_FIELD_FLAG = '/Ff'
ANNOT_VAL_KEY = '/V'
ANNOT_RECT_KEY = '/Rect'
PARENT_KEY = '/Parent'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'

def write_fillable_pdf(basename, data_dict, file_url):
    '''
    Generates a read-only PDF
    '''
    # Merge it with the original PDF
    ts = time.time()
    output_pdf_path = os.path.join(basename, 'filled/output_' + str(ts) + '.pdf')
    input_pdf_path = get_pdf_template(basename, file_url)
    #input_pdf_path = os.path.join(basename, 'template/SolarPanelTemplateTest.pdf')
    merge_pdf(input_pdf_path, output_pdf_path, data_dict)
    #os.remove(input_pdf_path) # done with template, remove it
    return output_pdf_path

def merge_pdf(input_pdf_path, output_pdf_path, data_dict):
    """
    Combine data with pdf tempate
    """
    try:
        template_pdf = pdfrw.PdfReader(input_pdf_path)
        if template_pdf:
            for page in template_pdf.pages:
                annotations = page[ANNOT_KEY]
                if annotations:
                    for annotation in annotations:
                        # only form fields matter
                        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                            # check for grouped radios
                            if annotation['/AS'] and annotation[PARENT_KEY] \
                                and annotation[PARENT_KEY][ANNOT_FIELD_TYPE] == '/Btn':
                                radio_button(annotation,  data_dict)
                            elif annotation[ANNOT_FIELD_KEY]:
                                key = annotation[ANNOT_FIELD_KEY].to_unicode()
                                if key_in_data_dict(key,data_dict):
                                    fill_field(annotation, data_dict, key)
                            #else some fields don't need to be filled

            template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
            pdfrw.PdfWriter().write(output_pdf_path, template_pdf)
            return output_pdf_path
    except pdfrw.errors.PdfParseError as pdf_error:
        raise Exception(f"Error reading pdf template: {pdf_error}")

def fill_field(annotation, data_dict, key):
    """
    Set form field values
    """
    ft = annotation[ANNOT_FIELD_TYPE]
    ff = annotation[ANNOT_FIELD_FLAG]

    if ft == '/Tx':
        text_form(annotation, str(data_dict[key]))
        annotation.update(pdfrw.PdfDict(AP=''))
    if ft == '/Ch':
        if ff and int(ff) & 1 << 17:  # test 18th bit
            combobox(annotation, data_dict[key])
            annotation.update(pdfrw.PdfDict(AP=''))
        #else:
            #listbox(annotation, data_dict[key])
    if ft == '/Btn':
        if ff and int(ff) & 1 << 15:  # test 16th bit
            radio_button(annotation, data_dict) #non-grouped radios
        else:
            checkbox(annotation, data_dict, key)

def key_in_data_dict(key, data_dict):
    """
    Check PDF form field in POST data
    """
    result = False
    for k, v in data_dict.items():
        if k==key:
            return True
        if type(data_dict[k]) is dict: # checkboxes
            result = key_in_data_dict(key, v)
    return result

def radio_button(annotation, data_dict):
    """
    Set radio button, need to set each grouped buttons to the value from request data
    """
    if annotation[PARENT_KEY]:
        key = annotation[PARENT_KEY][ANNOT_FIELD_KEY].to_unicode()
    else:
        key = annotation[ANNOT_FIELD_KEY].to_unicode()

    if key in data_dict:
        value  = data_dict[key]
        if '/N' in annotation['/AP']:
            selected = annotation['/AP']['/N'].keys()[1].strip(('/'))
            if selected == value:
                for data_key in data_dict:
                    if key == data_key:
                        annotation.update(pdfrw.PdfDict(V=pdfrw.objects.pdfname.BasePdfName(f'/{value}')))
                        annotation[PARENT_KEY].update(pdfrw.PdfDict(V=pdfrw.objects.pdfname.BasePdfName(f'/{value}')))

def checkbox(annotation, data_dict, key):
    """
    Set checkboxes
    """
    for k in data_dict:
        value=None
        if key in data_dict and type(data_dict[key]) is bool:
            value = data_dict[key]
        # grouped checkboxes
        elif type(data_dict[k]) is dict:
            for v_k in data_dict[k]:
                if v_k==key:
                    value = data_dict[k][v_k]
        if value and '/N' in annotation['/AP']:
            keys = annotation['/AP']['/N'].keys()
            if '/Off' in keys:
                keys.remove('/Off')
            export = keys[0]
            annotation.update(pdfrw.PdfDict(V=export, AS=export))

def combobox(annotation, value):
    """
    Set Drop Downs
    """
    export=None
    print(annotation['/Opt'])
    for each in annotation['/Opt']:
        if each.to_unicode()==str(value):
            export = each.to_unicode()
    pdfstr = pdfrw.objects.pdfstring.PdfString.encode(str(export))
    annotation.update(pdfrw.PdfDict(V=pdfstr, AS=pdfstr))

'''
def listbox(annotation, values):
    """
    Set multiple selections
    """
    print(annotation)
    pdfstrs=[]
    for value in values:
        export=None
        for each in annotation['/Opt']:
            if type(each) is pdfrw.objects.pdfarray.PdfArray:
                if each[1].to_unicode()==str(value):
                    export = each[1].to_unicode()
            elif each.to_unicode()==str(value):
                export = each.to_unicode()
        pdfstrs.append(pdfrw.objects.pdfstring.PdfString.encode(export))

    annotation.update(pdfrw.PdfDict(V=pdfstrs, AS=pdfstrs))
'''

def text_form(annotation, pdfstr):
    """
    Set Text
    """
    annotation.update(pdfrw.PdfDict(V=pdfstr, AS=pdfstr))

def get_pdf_template(basename, file_url):
    """
    Downloads data mapping from a source
    """
    r = requests.get(file_url, stream=True)
    chunk_size = 2000
    ts = time.time()
    template_pdf = os.path.join(basename, 'template/tmp_' + str(ts) + '.pdf')
    try:
        with open(template_pdf, 'wb') as fd:
            for chunk in r.iter_content(chunk_size):
                fd.write(chunk)
            fd.close()
            return template_pdf
    except Exception:
        raise Exception

def get_pdf_keys(template_pdf):
    """
    Helper function for generating pdf form field keys, debugging, etc.
    """

    template_pdf = pdfrw.PdfReader(template_pdf)
    annotations = template_pdf.pages[0][ANNOT_KEY]
    keys = {}
    for page in template_pdf.pages:
        annotations = page[ANNOT_KEY]
        if annotations is None:
            continue
        for annotation in annotations:
            if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                if annotation[ANNOT_FIELD_KEY]:
                    key = annotation[ANNOT_FIELD_KEY][1:-1]
                    type = annotation[ANNOT_FIELD_TYPE]
                    keys[key] = type
                elif annotation['/AS']:
                    parent_key = annotation[PARENT_KEY][ANNOT_FIELD_KEY][1:-1].strip('(').strip(')')
                    field = annotation['/AP']['/D'].keys()[1].strip('/')
                    if parent_key not in keys:
                        keys[parent_key] = {}
                        keys[parent_key]['type'] = 'BUTTONS'
                        keys[parent_key]['child'] = []
                        keys[parent_key]['annot_type'] = annotation[ANNOT_FIELD_TYPE]
                        keys[parent_key]['subtype'] = annotation[SUBTYPE_KEY]
                        keys[parent_key]['parentkey'] = annotation[PARENT_KEY][ANNOT_FIELD_KEY]

                    keys[parent_key]['child'].append(field)
    return keys
