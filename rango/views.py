from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from datetime import datetime

from rango.bing_search import run_query
from rango.forms import PageForm, CategoryForm, UserForm, UserProfileForm
from rango.models import Category, Page
from rango.utils import get_category_list

# Create your views here.

def index(request):
    # request.session.set_test_cookie()
    # if request.session.test_cookie_worked():
    #     print ">>>> TEST COOKIE WORKED!"
    #     request.session.delete_test_cookie()
    
    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    
    context_dict = {}
    context = RequestContext(request)
    context_dict['categories'] = category_list
    context_dict['pages'] = page_list

    ''' set Cookies '''
    # # Get the number of visits to the site.
    # # We use the COOKIES.get() function to obtain the visits cookie.
    # # If the cookie exists, the value returned is casted to an integer.
    # # If the cookie doesn't exist, we default to zero and cast that.
    # visits = int(request.COOKIES.get('visits', '1'))
    # reset_last_visit_time = False
    # # Does the cookie last_visit exist?
    # if 'last_visit' in request.COOKIES:
    #     # Yes it does! Get the cookie's value.
    #     last_visit = request.COOKIES['last_visit']
    #     # Cast the value to a Python date/time object.
    #     last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

    #     # If it's been more than a day since the last visit...
    #     if (datetime.now() - last_visit_time).seconds > 10:
    #         visits = visits + 1
    #         # ...and flag that the cookie last visit needs to be updated
    #         reset_last_visit_time = True
    # else:
    #     # Cookie last_visit doesn't exist, so flag that it should be set.
    #     reset_last_visit_time = True

    # if reset_last_visit_time:
    #     response.set_cookie('last_visit', datetime.now())
    #     response.set_cookie('visits', visits)
    
    # context_dict['visits'] = visits

    # #Obtain our Response object early so we can add cookie information.
    # response = render_to_response('rango/index.html', context_dict, context)


    ''' set Sessions '''
    visits = int(request.session.get('visits', '1'))
    reset_last_visit_time = False

    if 'last_visit' in request.session:
        last_visit = request.session['last_visit']
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 10:
            visits = visits + 1
            reset_last_visit_time = True
    else:
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    
    context_dict['visits'] = visits
    response = render_to_response('rango/index.html', context_dict, context)

    # Return response back to the user.
    return response


def about(request):
    context_dict = {}
    visits = int(request.session.get('visits', '1'))
    context_dict['visits'] = visits
    context = RequestContext(request)
    return render_to_response('rango/about.html', context_dict, context)


def category(request, category_name_url):
    context_dict = {}
    context = RequestContext(request)

    try:
        category = Category.objects.get(slug=category_name_url)
        context_dict['category_name'] = category.name
        # context_dict['category_name_url'] = category_name_url
        pages = Page.objects.filter(category=category).order_by('-views')
        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        pass

    context_dict['result_list'] = None
    context_dict['query'] = None

    if request.method == 'POST':
        query = request.POST.get('query').strip()
        if query:
            result_list = run_query(query)
            context_dict['result_list'] = result_list
            context_dict['query'] = query

    if not context_dict['query']:
        context_dict['query'] = category.name

    return render_to_response('rango/category.html', context_dict, context)

@login_required
def like_category(request):
    cat_id = None

    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = cat.likes+1
            cat.likes = likes
            cat.save()

    return HttpResponse(likes)


def add_category(request):
    context = RequestContext(request)
    context_dict = {}
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    context_dict['form'] = form

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', context_dict, context)


def add_page(request, category_name_url):

    context = RequestContext(request)
    context_dict = {}

    try:
        cat = Category.objects.get(slug=category_name_url)
    except Category.DoesNotExist:
        cat = None
    
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict['form'] = form
    context_dict['category'] = cat
    return render_to_response('rango/add_page.html', context_dict, context)


def register(request):
    context = RequestContext(request)
    context_dict = {}

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    context_dict['user_form'] = user_form
    context_dict['profile_form'] = profile_form
    context_dict['registered'] = registered

    return render_to_response('rango/register.html', context_dict, context)


def user_login(request):

    # if request.user.is_authenticated():
    #     return HttpResponseRedirect('/rango/')

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
                # We use request.POST.get('<variable>') as opposed to request.POST['<variable>'],
                # because the request.POST.get('<variable>') returns None, if the value does not exist,
                # while the request.POST['<variable>'] will raise key error exception
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                # return index(request)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        context = RequestContext(request)
        context_dict = {}
        return render_to_response('rango/login.html', context_dict, context)


def some_view(request):
    if not request.user.is_authenticated():
        return HttpResponse("You are logged in.")
    else:
        return HttpResponse("You are not logged in.")


def search(request):
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            # Run our Bing function to get the results list! 
            result_list = run_query(query)

    context_dict = {}
    context = RequestContext(request)
    context_dict['result_list'] = result_list

    return render_to_response('rango/search.html', context_dict, context)


@login_required
def restricted(request):
    context_dict = {}
    context = RequestContext(request)
    return render_to_response('rango/restricted.html', context_dict, context)


# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')


def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'

    if request.method == 'GET':
        if 'pageid' in request.GET:
            page_id = request.GET['pageid']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)

@login_required
def add_profile():
    pass


@login_required
def profile():
    pass


def suggest_category(request):
    context_dict = {}
    context = RequestContext(request)
    starts_with = ''

    if request.method == 'GET':
        starts_with = request.GET['suggestion']
    else:
        starts_with = request.POST['suggestion']

    cat_list = get_category_list(8, starts_with)
    context_dict['cat_list'] = cat_list

    return render_to_response('rango/category.html', context_dict, context)


@login_required
def auto_add_page(request):
    context_dict = {}
    context = RequestContext(request)

    cat_id = None
    url = None
    title = None

    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            page = Page.objects.get_or_create(category=category, title=title, url=url)
            pages = Page.objects.filter(category=category).order_by('-views')
            context_dict['pages'] = pages
    return render_to_response('rango/category.html', context_dict, context)
    pass
    


