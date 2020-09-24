from django.core.files.storage import FileSystemStorage
from moviepy.editor import *
from django.shortcuts import render, redirect
from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from .models import CredentialsModel
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from django.conf import settings
from http import client
import random
import time
import httplib2
from googleapiclient.errors import HttpError
# Create your views here.
#storage = DjangoORMStorage(GoogleAPIOauthInfo, 'id', request.user.id, 'credentials')
        #storage.put(credentials)
# all for the resumable upload
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, client.NotConnected,
    client.IncompleteRead, client.ImproperConnectionState,
    client.CannotSendRequest, client.CannotSendHeader,
    client.ResponseNotReady, client.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

global is_authorize
is_authorize = False

def home(request):
    return render(request,'yumakerapp/home.html')

def generate(request):
    print(is_authorize)
    if is_authorize == True:
        return render(request,'yumakerapp/generate.html')
    else:
        return redirect('login')

def login(request):
    global flow
    flow = OAuth2WebServerFlow(
    client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
    client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
    scope='https://www.googleapis.com/auth/youtube',
    redirect_uri='http://localhost:8000/oauth2callback/')

    authorize_url = flow.step1_get_authorize_url()
     #creates the authorization url to authorize the user
    return redirect(authorize_url)

def authorize(request):
    global credentials
    global is_authorize
    credentials = flow.step2_exchange(request.GET)
    storage = DjangoORMStorage(CredentialsModel,'id',request.user.id,'credentials')
    storage.put(credentials)
    is_authorize = True
    return redirect('generate')

def upload_video(request):
    # grabs image and audio and creates video
    if request.method == 'POST':
        image = request.FILES['image']
        audio = request.FILES['audio']

        title = request.POST['title']
        tag = request.POST['tag']
        description = request.POST['desc']
        catID = request.POST['cat']
        print(catID)


        status = request.POST['radio']


        fs = FileSystemStorage()
        fs.save(image.name, image)
        fs.save(audio.name, audio)

        image_path = str(fs.path(image.name))
        audio_path = str(fs.path(audio.name))

        a = AudioFileClip(audio_path)
        i = ImageClip(image_path).set_duration(a.duration)

        video = i.set_audio(a)

        video.write_videofile(f'{settings.MEDIA_ROOT}/video.mp4', fps=1, codec='libx264', audio_codec='aac',temp_audiofile='temp-audio.m4a', remove_temp=True)

        fs.delete(image.name)
        fs.delete(audio.name)

    client = build('youtube', 'v3', credentials=credentials)
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': [tag],
            'categoryId': catID
        },
        'status': {
            'privacyStatus': status
        }
    }
    insert_request = client.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(f'{str(settings.MEDIA_ROOT)}/video.mp4', chunksize=-1, resumable=True)
    )
    insert_request.execute()

    resumable_upload(request,insert_request)

    return render(request,'yumakerapp/success.html',context=context)

def resumable_upload(request,insert_request): #resume upload even when video upload runs into an error
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print()
            print( 'Uploading file...')
            status, response = insert_request.next_chunk()
            if response is not None:
                # print(response)
                if 'id' in response:
                    print( 'Video id "%s" was successfully uploaded.' % response['id'])
                    video_link = f'https://www.youtube.com/watch?v={response["id"]}'
                else:
                    exit('The upload failed with an unexpected response: %s' % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = 'A retriable error occurred: %s' % e

        if error is not None:
            print( error)
            retry += 1
            if retry > MAX_RETRIES:
                exit('No longer attempting to retry.')

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print( 'Sleeping %f seconds and then retrying...' % sleep_seconds)
            time.sleep(sleep_seconds)
    global context
    context = {
        'video_link':video_link
    }
