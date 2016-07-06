from django import forms
from django.contrib.admin import widgets
from invoicing.xero_utils import connect_to_xero


xero = connect_to_xero()


BDC_CHOICES = (
    ('', ''),
    ('BDC', 'BDC')
)
STATUS_CHOICES = (
    ('DRAFT', 'Draft'),
    ('SUBMITTED', 'Submitted'),
    ('AUTHORISED', 'Authorised'),
    ('DELETED', 'Deleted'),
    ('VOIDED', 'Voided')
)
NOK_OK_CHOICES = (
    ('NOK', 'NOK'),
    ('OK', 'OK')
)
STOCK_CHOICES = (
    ('', ''),
    ('BackOrder', 'Back order'),
    ('ActiveStock', 'Active stock')
)
PRODUCT_CHOICES = (
    ('SamGTab 9.7" BLACK', 'SamGTab 9.7" BLACK'),
    ('SamGTab 4 7" BLACK', 'SamGTab 4 7" BLACK'),
    ('SamGTab 4 7" PAPAYE', 'SamGTab 4 7" PAPAYE')
)
METHOD_CHOICES = (
    ('creditcard', 'Credit card'),
    ('check', 'Check'),
    ('cash', 'Cash'),
)
GENDER_CHOICES = (
    ('Mr', 'Monsieur'),
    ('Mme', 'Madame')
)
TAXTYPE_CHOICES = (
    ('Tax on Sales / Handicap', 'Tax on Sales / Handicap'),
    ('Tax on Sales', 'Tax on Sales'),
    ('OUTPUT', 'OUTPUT'),
)
ADDRESSTYPE_CHOICES = (
    ('POBOX', 'POBOX'),
    ('STREET', 'STREET'),
    ('DELIVERY', 'DELIVERY'),
)
LINEAMOUNTTYPES_CHOICES = (
    ('Exclusive', 'Exclusive'),
    ('Inclusive', 'Inclusive'),
    ('NoTax', 'No tax'),
)
INVOICETYPE_CHOICES = (
    ('ACCREC', 'ACCREC'),
    ('ACCPAY', 'ACCPAY'),
)

CURRENCY_CHOICES = []
for currency in xero.currencies.all():
    CURRENCY_CHOICES.append((currency['Code'], currency['Description'] + ' / ' + currency['Code']))
CURRENCY_CHOICES = tuple(CURRENCY_CHOICES)

BRANDING_THEME_CHOICES = []
for brandingtheme in xero.brandingthemes.all():
    BRANDING_THEME_CHOICES.append((brandingtheme['BrandingThemeID'], brandingtheme['Name']))
BRANDING_THEME_CHOICES = tuple(BRANDING_THEME_CHOICES)

ACCOUNTCODE_CHOICES = []
for account in xero.accounts.all():
    if 'Code' in account:
        ACCOUNTCODE_CHOICES.append((account['Code'], account['Code'] + '/' + account['Type']))
ACCOUNTCODE_CHOICES = tuple(ACCOUNTCODE_CHOICES)


class OrderForm(forms.Form):
    bdc = forms.ChoiceField(label='BDC', choices=BDC_CHOICES)
    code = forms.IntegerField(label='CODE')
    email = forms.EmailField(label='E-mail')
    status = forms.ChoiceField(choices=STATUS_CHOICES)
    reception = forms.DateField(widget=widgets.AdminDateWidget)
    payment = forms.DateField(widget=widgets.AdminDateWidget)
    ship_sheduled = forms.DateField(label='Ship sheduled', widget=widgets.AdminDateWidget)
    shipping = forms.DateField(widget=widgets.AdminDateWidget)
    cancellation = forms.DateField(widget=widgets.AdminDateWidget)
    confirmed_paid = forms.ChoiceField(label='Confirmed paid', choices=NOK_OK_CHOICES)
    invoiced = forms.ChoiceField(choices=NOK_OK_CHOICES)
    stock_from = forms.ChoiceField(label='Stock from', choices=STOCK_CHOICES)
    product = forms.ChoiceField(choices=PRODUCT_CHOICES)
    paid = forms.DecimalField(decimal_places=2, help_text='€')
    method = forms.ChoiceField(choices=METHOD_CHOICES)
    comments = forms.CharField()
    telephone = forms.CharField(label='Téléphone')
    gender = forms.ChoiceField(choices=GENDER_CHOICES)
    prenom = forms.CharField()
    nom = forms.CharField()
    organisme = forms.CharField()
    adresse = forms.CharField(label='Adresse ligne 1 & 2')
    code_postal = forms.IntegerField(label='CP')
    ville = forms.CharField()
    pays = forms.CharField()


class InvoiceForm(forms.Form):
    InvoiceID = forms.CharField(required=False, widget=forms.HiddenInput)
    Type = forms.ChoiceField(label='Invoice type', choices=INVOICETYPE_CHOICES)
    InvoiceNumber = forms.CharField(required=False, label='Invoice number', disabled=True,
                                    widget=forms.TextInput(attrs={'placeholder': 'Auto generated'}))
    Status = forms.ChoiceField(choices=STATUS_CHOICES)
    Reference = forms.CharField(required=False, disabled=True)
    Date = forms.DateField(label='Invoice date', widget=widgets.AdminDateWidget,
                           input_formats=['%Y-%m-%d'])
    DueDate = forms.DateField(label='Due date', widget=widgets.AdminDateWidget,
                              input_formats=['%Y-%m-%d'])
    LineAmountTypes = forms.ChoiceField(label='Line amount types', choices=LINEAMOUNTTYPES_CHOICES)
    # SubTotal = forms.DecimalField(label='Sub total', help_text='Total of invoice excluding taxes.')
    # Total = forms.DecimalField(help_text='€')

    CurrencyCode = forms.ChoiceField(label='Currency', choices=CURRENCY_CHOICES)
    BrandingThemeID = forms.ChoiceField(label='Branding theme', choices=BRANDING_THEME_CHOICES)


class SimpleInvoiceForm(forms.Form):
    InvoiceID = forms.CharField(required=True, widget=forms.HiddenInput)
    InvoiceNumber = forms.CharField(required=True, label='Invoice number')


class ContactForm(forms.Form):
    ContactID = forms.CharField(required=False, widget=forms.HiddenInput)
    Name = forms.CharField(help_text='Full name of contact/organisation')
    LastName = forms.CharField(required=False, label='Last name')
    FirstName = forms.CharField(required=False, label='First name')
    EmailAddress = forms.EmailField(required=False, label='Email address')


class AddressForm(forms.Form):
    AddressType = forms.ChoiceField(label='Address type', choices=ADDRESSTYPE_CHOICES)
    AddressLine1 = forms.CharField(label='PO Address line 1')
    AddressLine2 = forms.CharField(required=False, label='PO Address line 2')
    AddressLine3 = forms.CharField(required=False, label='PO Address line 3')
    AddressLine4 = forms.CharField(required=False, label='PO Address line 4')
    PostalCode = forms.IntegerField(label='PO postal code')
    City = forms.CharField(label='PO City')
    Region = forms.CharField(required=False, label='PO region')
    Country = forms.CharField(required=False, label='PO country')


class LineItemForm(forms.Form):
    LineItemID = forms.CharField(required=False, widget=forms.HiddenInput)
    Description = forms.CharField()
    Quantity = forms.DecimalField()
    UnitAmount = forms.DecimalField(label='Unit amount')
    #DiscountRate = forms.DecimalField(label='Discount rate')
    AccountCode = forms.ChoiceField(required=False, label='Account code',
                                    choices=ACCOUNTCODE_CHOICES)
    #TaxType = forms.ChoiceField(label='Tax type', choices=TAXTYPE_CHOICES)


class SimpleAccountForm(forms.Form):
    AccountID = forms.CharField(required=True, widget=forms.HiddenInput)
    Name = forms.CharField(required=True, label='Account name')


class PaymentForm(forms.Form):
    Date = forms.DateField(input_formats=['%Y-%m-%d'], widget=widgets.AdminDateWidget)
    Amount = forms.DecimalField()
    Reference = forms.CharField(required=False, help_text='Payment method')
