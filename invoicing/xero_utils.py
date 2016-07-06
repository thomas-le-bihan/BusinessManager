import uuid
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, Http404
from xero import Xero
from xero.auth import PrivateCredentials

from local_settings import CONSUMER_KEY, PRIVATEKEY_PATH


INVOICE_FIELDS = (
    'InvoiceID', 'ID1', 'ID2', 'status', 'PAID',
    'INVOICED', 'Accounting_month', 'LastName',
    'FirstName', 'EmailAddress', 'InvoiceNumber',
    'Reference', 'InvoiceDate', 'DueDate', 'Total',
    'CurrencyCode', 'BrandingThemeID'
)
ADDRESS_FIELDS = (
    'AddressLine1', 'AddressLine2', 'AddressLine3',
    'AddressLine4', 'PostalCode', 'City', 'Region',
    'Country',
)
LINEITEM_FIELDS = (
    'LineItemID', 'ItemCode', 'Description', 'Quantity',
    'UnitAmount', 'DiscountRate', 'AccountCode', 'TaxType',
    'TaxAmount', 'TrackingName1', 'TrackingOption1',
    'TrackingName2', 'TrackingOption2',
)


def connect_to_xero():
    """
    Connect to a private application
    :return: xero object to access xero datas
    """
    with open(PRIVATEKEY_PATH) as keyfile:
        rsa_key = keyfile.read()
    credentials = PrivateCredentials(CONSUMER_KEY, rsa_key)
    return Xero(credentials)


def get_invoices(page, per_page=10):
    xero = connect_to_xero()
    all_invoices = xero.invoices.filter(order='InvoiceNumber')
    paginator = Paginator(all_invoices, per_page)
    try:
        invoices = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        invoices = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        invoices = paginator.page(paginator.num_pages)
    return invoices


def get_invoice_pdf(id):
    xero = connect_to_xero()
    try:
        # Fetch a PDF
        invoice = xero.invoices.filter(InvoiceID=id)
        invoice_pdf = xero.invoices.get(id, headers={'Accept': 'application/pdf'})
        # Stream the PDF to the user (Django specific example)
        response = HttpResponse(invoice_pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s.pdf"'\
                                          %(invoice[0]['InvoiceNumber'])
    except Exception as e:
        raise Http404(str(e))
    return response


def get_invoice_for_id(id):
    xero = connect_to_xero()
    return xero.invoices.get(id)[0]


def get_account_for_id(id):
    xero = connect_to_xero()
    return xero.accounts.get(id)[0]


def get_contact_for_id(id):
    xero = connect_to_xero()
    return xero.contacts.get(id)[0]


def create_or_update_contact(data):
    xero = connect_to_xero()

    # Check if contact exists
    contact = xero.contacts.filter(Name=data['Name'])
    if len(contact) > 0:
        # modify contact
        data['ContactID'] = contact[0]['ContactID']
        #print(data)
        for field in data:
            contact[0][field] = data[field]
        contact = xero.contacts.save(contact)
    else:
        # create new contact
        del data['ContactID']
        contact = xero.contacts.put(data)
    return contact[0]['ContactID']


def create_or_update_invoice(data):
    xero = connect_to_xero()

    if 'InvoiceID' in data and data['InvoiceID'] != '':
        # modify invoice
        invoice = xero.invoices.get(data['InvoiceID'])
        for field in data:
            invoice[0][field] = data[field]
        print(data)
        invoice = xero.invoices.save(invoice)
    else:
        # create new invoice
        del data['InvoiceID']
        del data['InvoiceNumber']
        for lineitem in data['LineItems']:
            del lineitem['LineItemID']
        print(data)
        invoice = xero.invoices.put(data)
    return invoice[0]['InvoiceID']


def create_payment(data):
    xero = connect_to_xero()
    return xero.payments.put(data)[0]