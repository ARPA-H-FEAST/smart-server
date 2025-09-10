from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse

import json
import logging
import os


def get_data_sources(request): ...
