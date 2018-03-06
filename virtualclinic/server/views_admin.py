from csv import QUOTE_MINIMAL, writer
import re

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.db.utils import IntegrityError

from server.forms import SpecialityForm, EmployeeRegistrationForm, ImportForm, ExportForm, HospitalForm, StatisticsForm
from server.models import Speciality, Account, Action, Hospital, Location, Statistics
from server import logger
from server import views


def users_view(request):
    # Authentication check.
    authentication_result = views.authentication_check(request, [Account.ACCOUNT_ADMIN])
    if authentication_result is not None: return authentication_result
    # Get the template data from the session
    template_data = views.parse_session(request)
    # Proceed with the rest of the view
    if request.method == 'POST':
        pk = request.POST['pk']
        role = request.POST['role']
        account = Account.objects.get(pk=pk)
        if account is not None:
            account.role = role
            account.save()
            logger.log(Action.ACTION_ADMIN,'Admin modified ' + account.user.username + "'s role", request.user.account)
            template_data['alert_success'] = "Updated" + account.user.username + "'s role!"
    # Parse search sorting
    template_data['query'] = Account.objects.all().order_by('-role')
    return render(request,'virtualclinic/admin/users.html', template_data)


def activity_view(request):
    # Authentication check.
    authentication_result = views.authentication_check(request, [Account.ACCOUNT_ADMIN])
    if authentication_result is not None: return authentication_result
    # Get the template data from the session
    template_data = views.parse_session(request)
    # Proceed with the rest of the view
    # Parse search sorting
    template_data['query'] = Action.objects.all().order_by('-timePerformed')
    return render(request,'virtualclinic/admin/activity.html',template_data)


# Do speciality view
def speciality_view(request):
    # Authentication check.
    authentication_result = views.authentication_check(request, [Account.ACCOUNT_ADMIN])
    if authentication_result is not None: return authentication_result
    # Get the template data from the session
    template_data = views.parse_session(request)
    # Proceed with the rest of the view

    return render(request,'virtualclinic/admin/',template_data)

def add_speciality(request):
    # Authentication check
    authentication_result = views.authentication_check(request,[Account.ACCOUNT_ADMIN])
    if authentication_result is not None: 
        return authentication_result
    # Get template data from the session
    template_data = views.parse_session(
        request,
        {'form_button' : "Add Speciality"}
    )
    # Proceed with the rest of the view
    if request.method == 'POST':
        form = SpecialityForm(request.POST)
        if form.is_valid():
            speciality = Speciality(
                name = form.cleaned_data['name'],
                description = form.cleaned_data['description']
            )
            speciality.save()
            form = SpecialityForm()     # Clean the form when page is redisplayed
            template_data['alert_success'] = "Successfully added the Speciality!"
            logger.log(Action.ACTION_ADMIN, 'Admin added '+ speciality.name, speciality.description)
    else:
        form = SpecialityForm()
    template_data['form'] = form
    return render(request,'virtualclinic/admin/add_speciality.html', template_data)


def add_hospital_view(request):
    # Authentication check.
    authentication_result = views.authentication_check(
        request,
        [Account.ACCOUNT_ADMIN]
    )
    if authentication_result is not None: return authentication_result
    # Get the template data from the session
    template_data = views.parse_session(
        request,
        {'form_button':"Add Hospital"}
    )
    # Proceed with the rest of the view
    if request.method == 'POST':
        form = HospitalForm(request.POST)
        if form.is_valid():
            location = location(
                city = form.cleaned_data['city'],
                zip = form.cleaned_data['zip'],
                state = form.cleaned_data['state'],
                address = form.cleaned_data['address']
            )
            location.save()
            hospital = Hospital(
                name = form.cleaned_data['name'],
                phone = form.cleaned_data['phone'],
                location = location,
            )
            hospital.save()
            form = HospitalForm()   # Clean the form when page is redisplayed
            template_data['alert_success'] = "Successfully added the hospital!"
    else:
        form = HospitalForm()
    template_data['form'] = form
    return render(request,'virtualclinic/admin/add_hospital.html', template_data)


def createemployee_view(request):
    # Authentication check.
    authentication_result = views.authentication_check(request, [Account.ACCOUNT_ADMIN])
    if authentication_result is not None: return authentication_result
    # Get the template data from the session
    template_data = views.parse_session(request,{'form_button':"Register"})
    # Proceed with the rest of the view
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            user = views.register_user(
                form.cleaned_data['email'],
                form.cleaned_data['password_first'],
                form.cleaned_data['firstname'],
                form.cleaned_data['lastname'],
                form.cleaned_data['employee']
            )
            logger.log(Action.ACTION_ADMIN, 'Admin registered '+ user.username, request.user.account)
            request.session['alert_success'] = "Successfully created new employee account"
            return HttpResponseRedirect('/admin/users/')
    else:
        form = EmployeeRegistrationForm()
    template_data['form'] = form
    return render(request,'virtualclinic/admin/createemployee.html', template_data)


def statistic_view(request):
    # Authentication check.
    authentication_result = views.authentication_check(request, [Account.ACCOUNT_ADMIN])
    if authentication_result is not None: return authentication_result
    # Get the template data from the session
    template_data = views.parse_session(request,{'form_button':"Get Statistics"})
    # Proceed with the rest of the view
    default = {}
    request.POST._mutable = True
    request.POST.update(default)
    predate_filter = Action.objects.all()
    template_data['pre_filter'] = predate_filter.count()
    form = StatisticsForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            statistics = Statistics(
                startDate = form.cleaned_data['startDate'],
                endDate = form.cleaned_data['endDate'],
            )
            date_filter = Action.objects.all().filter(timePerformed__range = (statistics.startDate,statistics.endDate))
            template_data['temp'] = date_filter.count()
            template_data['start'] = statistics.startDate
            template_data['end'] = statistics.endDate

            template_data['total_logins'] = Action.objects.filter(description__icontains="Account login",timePerformed__range = (statistics.startDate, statistics.endDate) ).count()
            template_data['total_logouts'] = Action.objects.filter(description__icontains="Account logout",timePerformed__range = (statistics.startDate, statistics.endDate)).count()
            template_data['total_admitted'] = Action.objects.filter(description__icontains="Admitted Patient",timePerformed__range = (statistics.startDate, statistics.endDate)).count()
            template_data['total_discharged'] = Action.objects.filter(description__icontains="Discharged Patient",timePerformed__range = (statistics.startDate, statistics.endDate)).count()
            template_data['total_appointments'] = Action.objects.filter(description__icontains="Appointment created",timePerformed__range = (statistics.startDate, statistics.endDate)).count()
            template_data['total_med_tests'] = Action.objects.filter(description__icontains="Medical Test created",timePerformed__range = (statistics.startDate, statistics.endDate)).count()
            template_data['total_registered'] = Action.objects.filter(description__icontains="registered",timePerformed__range = (statistics.startDate, statistics.endDate)).count()

    else:
        form._errors = {}
        statistics = Statistics(
                startDate = 0,
                endDate = 0,
            )
        errdate_filter = Action.objects.all()
        template_data['errdate_filter'] = errdate_filter.count()
        template_data['start'] = statistics.startDate
        template_data['end'] = statistics.endDate

        template_data['total_logins'] = 0
        template_data['total_logouts'] = 0
        template_data['total_admitted'] = 0
        template_data['total_discharged'] = 0
        template_data['total_appointments'] = 0
        template_data['total_med_tests'] = 0
        template_data['total_registered'] = 0
    template_data['form'] =form

    return render(request,'virtualclinic/admin/statistics.html', template_data)

def csv_import_view(request):
    # Authentication check.
    authentication_result = views.authentication_check(request, [Account.ACCOUNT_ADMIN])
    if authentication_result is not None: return authentication_result
    template_data = views.parse_session(request, {'form_button': "Submit"})
    if request.method=='POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['upload']
            for line in file:
                first_word = re.split('[,]',line.decode("utf-8").strip())[0].lower()
                if first_word == 'firstname':
                    count = handle_user_csv(file)
                    m = str(count[0])+' users are successfully uploaded, '+str(count[1])+' duplicate accounts.'
                    if count[0] == 0:
                        template_data['alert_danger'] = m
                    else:
                        template_data['alert_success'] = m
                elif first_word=='name':
                    count = handle_hospital_csv(file)
                    m = str(count[0])+' hospitals are successfully uploaded, '+str(count[1])+' duplicate hospitals.'
                    if count[0] == 0:
                        template_data['alert_danger'] = m
                    else:
                        template_data['alert_success'] = m
                else:
                    template_data['alert_danger'] = "Invalid CSV format."
                template_data['form'] = form
                return render(request,'virtualclinic/admin/import.html', template_data)
        else:
            template_data['alert_danger'] = "Please choose a file to upload"
    form = ImportForm()
    template_data['form'] = form
    return render(request,'virtualclinic/admin/import.html',template_data)


def handle_user_csv(f):
    """
    Handles a CSV containing User information.
    The first row should contain the following information
        FirstName,LastName,Account,Username,Email,Hospital
    with the following lines containing information about zero or more Users.
    :param f: The file object containing the CSV
    :return: The # of successes and failures
    """
    success = 0
    fail = 0
    is_first = True
    for row in f:
        if is_first:
            is_first=False
            continue    # breaks out of for loop
        line = re.split('[,]',row.decode("utf-8").strip())
        if line[0]:
            f_name = line[0]
            l_name = line[1]
            role = line[2].lower()
            username = line[3].lower()
            try:
                if role== "doctor":
                    views.register_user(
                        username,'password',f_name,l_name,
                        Account.ACCOUNT_DOCTOR,
                    )
                elif role == "admin":
                    views.register_user(
                        username, 'password', f_name, l_name,
                        Account.ACCOUNT_ADMIN,
                    )
                else:
                    views.register_user(
                        username, 'password', f_name, l_name,
                        Account.ACCOUNT_PATIENT,
                    )
                success+=1
            except (IntegrityError, ValueError):
                fail+=1
                continue
    return success,fail


def handle_hospital_csv(f):
    """
    Handles a CSV containing Hospital information.
    The first row should contain the following information:
        Name
    with the following lines containing information about zero or more Hospitals.
    :param f: The file containing the CSV
    :return: The # of successes and failures
    """
    success = 0
    fail = 0
    is_first = True
    for row in f:
        if is_first:
            is_first = False
            continue
        line = re.split('[,]',row.decode("utf-8").strip())
        if line[0]:
            hosp = line[0]
            address = line[1]
            city = line[2]
            state = line[3]
            zip = line[4]
            phone = line[5]
            try:
                location = Location(
                    city = city,
                    zip = zip,
                    state = state,
                    address = address
                )
                location.save()
                hospital = Hospital(
                    name = hosp,
                    phone = phone,
                    location = location,
                )
                hospital.save()
                success+=1
            except (IntegrityError, ValueError):
                fail+=1
                continue
    return success, fail


def csv_export_view(request):
    # Authentication check
    authentication_result = views.authentication_check(request,[Account.ACCOUNT_ADMIN])
    if authentication_result is not None:
        return authentication_result
    template_data = views.parse_session(request,{'form_button':"Submit"})
    if request.method == 'POST':
        if request.POST['export'] == 'hospitals':
            return generate_hospital_csv()
        elif request.POST['export'] == 'users':
            return generate_user_csv()
        else:
            template_data['alert_danger'] = 'Please choose a file to download'
    template_data['form'] = ExportForm()
    return render(request,'virtualclinic/admin/export.html', template_data)


def generate_user_csv():
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    write = writer(response, delimeter=',', quotechar='"', quoting=QUOTE_MINIMAL)
    write.writerow(['FirstName', 'LastName', 'Role', 'Username'])
    for a in Account.objects.all():
        firstname = a.profile.firstname
        lastname = a.profile.lastname
        role = a.role
        username = a.profile.username
        if role== 10:
            role = 'Patient'
        elif role == 20:
            role='Doctor'
        elif role== 30:
            role='Admin'
        else:
            role='Unknown'
        write.writerow([firstname,lastname,role,username])
    return response


def generate_hospital_csv():
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hospitals.csv"'
    write = writer(response,delimeter=',', quotechar='"',quoting=QUOTE_MINIMAL)
    write.writerow(['Name','Address','City','State','Zip','Phone'])
    for h in Hospital.objects.all():
        write.writerow([h.name,h.location.address,h.location.city,h.location.state,h.location.zip,h.phone])
    return response