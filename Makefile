#build and deploy
#
TARGET=main
#
-include .env
CONFIG_DIR=./config/gcp
#-------------------------------------------------------------------------------
# Input Parameter
#-------------------------------------------------------------------------------
PLATFORM=GCP
REGION=asia-northeast1
PROJECT_ID=ats-ai-genaiapp-internal
REPOSITORY=docker-repo-prod
ifeq "$(TARGET)" "main"
	SERVICE_NAME='llmdemo'
	IMAGE_NAME=main-image
	REDIRECT_URI="https://llmdemo-xuurtmv7ha-an.a.run.app"
else ifeq "$(TARGET)" "dev"
	SERVICE_NAME='llmdemo-dev'
	IMAGE_NAME=dev-image
	REDIRECT_URI="https://llmdemo-dev-xuurtmv7ha-an.a.run.app"
endif
IMAGE_URL=$(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPOSITORY)/$(IMAGE_NAME):runner
#-------------------------------------------------------------------------------
#
IMAGE_PATH=$\
	_PLATFORM=$(PLATFORM),$\
	_REGION=$(REGION),$\
	_PROJECT_ID=$(PROJECT_ID),$\
	_REPOSITORY=$(REPOSITORY),$\
	_IMAGE_NAME=$(IMAGE_NAME)
#
SECRET_KEY=$\
	_GOOGLE_CLIENT_ID=$(GOOGLE_CLIENT_ID),$\
	_GOOGLE_CLIENT_SECRET=$(GOOGLE_CLIENT_SECRET),$\
	_REDIRECT_URI=$(REDIRECT_URI),$\
	_OPENAI_API_KEY=${OPENAI_API_KEY},$\
	_AZURE_API_BASE=${AZURE_API_BASE},$\
	_AZURE_API_KEY1=${AZURE_API_KEY1},$\
	_AZURE_API_KEY2=${AZURE_API_KEY2}

.PHONY: init create build_full build_cache deploy describe

run: export TARGET:=$(TARGET)
run: export PLATFORM:="local"
run:
	cd ./app/streamlit && \
	poetry run streamlit run main.py --server.port 8080 --browser.gatherUsageStats false

create:
	gcloud artifacts repositories create $(REPOSITORY) \
	--repository-format=docker --location=$(REGION) \
	--description="$(REPOSITORY)"
	gcloud artifacts repositories list

build_full:
	gcloud builds submit \
	--config ${CONFIG_DIR}/cloudbuild_full.yaml \
	--substitutions=_TARGET=$(TARGET),$(IMAGE_PATH),$(SECRET_KEY)

build_cache:
	gcloud builds submit \
	--config ${CONFIG_DIR}/cloudbuild_cache.yaml \
	--substitutions=_TARGET=$(TARGET),$(IMAGE_PATH),$(SECRET_KEY)

deploy:
	gcloud run deploy $(SERVICE_NAME) \
	--image $(IMAGE_URL) --region=$(REGION) \
	--service-account=$(SERVICE_ACCOUNT) \
	--session-affinity --allow-unauthenticated \
	--port=8080 --timeout=3600 \
	--concurrency=80 --max-instances=5 --cpu=2000m --memory=4Gi
#	--set-env-vars _TARGET=$(TARGET),_PLATFORM=$(PLATFORM),$(SECRET_KEY) \

describe:
	gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format export

requirements:
	poetry export -f requirements.txt -o requirements.txt --without-hashes

archive:
	git archive --format=tar.gz --output=./llmdemo.tar.gz HEAD
