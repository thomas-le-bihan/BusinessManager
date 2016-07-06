from email.mime.base import MIMEBase
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.template import Context
from django.template.loader import render_to_string
from AuticielBusinessManager.settings import EMAIL_HOST_USER

from invoicing.forms import InvoiceForm, LineItemForm, AddressForm, ContactForm, \
    SimpleAccountForm, SimpleInvoiceForm, PaymentForm
from invoicing.xero_utils import get_invoice_for_id, create_or_update_invoice, \
    get_invoice_pdf, get_invoices, create_or_update_contact, get_account_for_id, create_payment, get_contact_for_id


def list_invoice(request):
    page = 1
    if request.method == 'GET' and 'page' in request.GET:
        page = request.GET['page']
    invoices = get_invoices(page)

    context = {
        'title': 'Invoices list',
        'invoices': invoices,
        'page_list': range(1, invoices.paginator.num_pages)
    }

    return render(request, 'invoicing/list.html', context)


def edit_invoice(request):

    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST)
        contact_form = ContactForm(request.POST)
        nb_items = int(request.POST['nb_item'])
        if "additem" in request.POST:
            nb_items += 1
        nb_addresses = int(request.POST['nb_address'])
        if "addaddress" in request.POST:
            nb_addresses += 1
        lineitem_datas = request.POST.dict()
        lineitem_datas.update({
            'form-TOTAL_FORMS': str(nb_items),
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',})
        LineItemFormSet = formset_factory(LineItemForm, extra=nb_items, can_delete=True)
        lineitem_formset = LineItemFormSet(lineitem_datas)
        address_datas = request.POST.dict()
        address_datas.update({
            'form-TOTAL_FORMS': str(nb_addresses),
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',})
        AddressFormSet = formset_factory(AddressForm, extra=nb_addresses)
        address_formset = AddressFormSet(address_datas)
        if invoice_form.is_valid() \
                and contact_form.is_valid()\
                and lineitem_formset.is_valid()\
                and address_formset.is_valid():

            contact_cleaneddatas = contact_form.cleaned_data
            contact_cleaneddatas['Addresses'] = []
            for form in address_formset:
                contact_cleaneddatas['Addresses'].append(form.cleaned_data)

            invoice_cleaneddatas = invoice_form.cleaned_data
            invoice_cleaneddatas['LineItems'] = []
            for form in lineitem_formset:
                lineitem_cleaneddatas = form.cleaned_data
                del lineitem_cleaneddatas['DELETE']
                invoice_cleaneddatas['LineItems'].append(lineitem_cleaneddatas)

            contact_id = create_or_update_contact(contact_cleaneddatas)
            invoice_cleaneddatas['Contact'] = {'ContactID': contact_id}
            create_or_update_invoice(invoice_cleaneddatas)

            messages.add_message(request, messages.INFO,
                                 'Invoice ' + str(123456) +
                                 ' successfully created.')
            return HttpResponseRedirect('/invoice/')
    elif request.method == 'GET' and 'invoice_id' in request.GET:
        invoice_id = request.GET['invoice_id']
        invoice = get_invoice_for_id(invoice_id)
        lineitems = invoice['LineItems']
        contact = invoice['Contact']
        addresses = contact['Addresses']
        nb_items = len(lineitems)
        nb_addresses = len(addresses)

        invoice.update(contact)

        lineitem_datas = {
            'form-TOTAL_FORMS': str(nb_items),
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',}
        cpt = 0
        for item in lineitems:
            for field in item:
                lineitem_datas['form-'+str(cpt)+'-'+field] = item[field]
            cpt += 1

        address_datas = {
            'form-TOTAL_FORMS': str(nb_addresses),
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',}
        cpt = 0
        for address in addresses:
            for field in address:
                address_datas['form-'+str(cpt)+'-'+field] = address[field]
            cpt += 1

        invoice_form = InvoiceForm(invoice)
        contact_form = ContactForm(contact)
        LineItemFormSet = formset_factory(LineItemForm, can_delete=True)
        lineitem_formset = LineItemFormSet(lineitem_datas)
        AddressFormSet = formset_factory(AddressForm)
        address_formset = AddressFormSet(address_datas)
    else:
        invoice_form = InvoiceForm()
        contact_form = ContactForm()
        lineitem_formset = formset_factory(LineItemForm, can_delete=True)
        address_formset = formset_factory(AddressForm)

    context = {
        'title': 'Edit invoice',
        'invoice_form': invoice_form,
        'contact_form': contact_form,
        'lineitem_formset': lineitem_formset,
        'address_formset': address_formset,
    }
    return render(request, 'invoicing/edit.html', context)


def pdf_invoice(request):
    if 'invoice_id' in request.GET:
        invoice_id = request.GET['invoice_id']
        response = get_invoice_pdf(invoice_id)
    else:
        raise Http404('Missing invoice id')
    return response


def mail_invoice(request):

    if request.method == 'POST':
        if 'submit' in request.POST\
                and 'mail' in request.POST:
            submit = request.POST['submit']
            mail = request.POST['mail']
            invoice_id = request.POST['invoice_id']
            invoice = get_invoice_for_id(invoice_id)
            if submit == 'Send':
                invoice_pdf = get_invoice_pdf(invoice_id).content

                email = EmailMessage('Auticiel invoice')
                email.body = 'Hello, Please find the invoice in attachments.'
                email.from_email = EMAIL_HOST_USER
                email.to = [mail,]
                email.attach(invoice['InvoiceID']+'.pdf',
                                     invoice_pdf,
                                     'application/pdf')
                email.send()

                messages.add_message(request, messages.INFO,
                                     'Invoice ' + invoice['InvoiceNumber'] +
                                     ' successfully mailed to' + mail + '.')
                return HttpResponseRedirect('/invoice/')
            else:  # Cancel
                return HttpResponseRedirect('/invoice/')
        else:
            return HttpResponseBadRequest('Missing arg')
    elif request.method == 'GET':
        if 'invoice_id' in request.GET:
            invoice_id = request.GET['invoice_id']
            invoice = get_invoice_for_id(invoice_id)
            contact = get_contact_for_id(invoice['Contact']['ContactID'])

            if contact['EmailAddress'] == "":
                messages.add_message(request, messages.WARNING,
                                     'Contact does not specified an email address')
                return HttpResponseRedirect('/invoice/')
        else:
            return HttpResponseBadRequest('Missing arg')

    context = {
        'title': 'Mail',
        'invoice_id': invoice_id,
        'mail': contact['EmailAddress'],
    }

    return render(request, 'invoicing/mail.html', context)


def pay_invoice(request):

    if request.method == 'POST':
        simpleinvoice_form = SimpleInvoiceForm(request.POST)
        simpleaccount_form = SimpleAccountForm(request.POST)
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid()\
                and simpleaccount_form.is_valid()\
                and simpleinvoice_form.is_valid():
            payment_data = {
                'Invoice': {'InvoiceID': simpleinvoice_form.cleaned_data['InvoiceID']},
                'Account': {'AccountID': simpleaccount_form.cleaned_data['AccountID']},
            }
            payment_data.update(payment_form.cleaned_data)

            messages.add_message(request, messages.INFO,
                                 'Payment for invoice ' +
                                 simpleinvoice_form.cleaned_data['InvoiceID'] +
                                 ' successfully created.')
            return HttpResponseRedirect('/invoice/')
    else:
        invoice_id = request.GET['selected_invoice']

        invoice = get_invoice_for_id(invoice_id)
        account = get_account_for_id('ce3871b3-60c6-4cf3-8474-3bbb96181a98')

        simpleinvoice_form = SimpleInvoiceForm(invoice)
        simpleaccount_form = SimpleAccountForm(account)
        payment_form = PaymentForm()

    context = {
        'title': 'Payment',
        'simpleinvoice_form': simpleinvoice_form,
        'simpleaccount_form': simpleaccount_form,
        'payment_form': payment_form,
    }
    return render(request, 'invoicing/pay.html', context)
