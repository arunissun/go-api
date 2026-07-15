from rest_framework import serializers


class DocumentContextSerializer(serializers.Serializer):
    countryOrOperationName = serializers.CharField(required=False, allow_blank=True, default="")
    countryId = serializers.IntegerField(required=False, allow_null=True)
    countryIso = serializers.CharField(required=False, allow_blank=True, default="")
    countryIso3 = serializers.CharField(required=False, allow_blank=True, default="")
    countryName = serializers.CharField(required=False, allow_blank=True, default="")
    countryCentroid = serializers.DictField(required=False, allow_null=True)
    countryBoundingBox = serializers.ListField(
        child=serializers.FloatField(), required=False, allow_null=True, min_length=4, max_length=4
    )
    operationTitle = serializers.CharField(required=False, allow_blank=True, default="")
    hazardTypes = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    eapName = serializers.CharField(required=False, allow_blank=True, default="")
    eapVariant = serializers.CharField(required=False, allow_blank=True, default="")
    versionLabel = serializers.CharField(required=False, allow_blank=True, default="")
    displayTitleOverrideEnabled = serializers.BooleanField(required=False, default=False)
    displayTitleOverride = serializers.CharField(required=False, allow_blank=True, default="")
    interPhasePreToAct = serializers.CharField(required=False, allow_blank=True, default="PRECEDES")
    interPhaseActToStop = serializers.CharField(required=False, allow_blank=True, default="ENABLES")


class StatementDraftSerializer(serializers.Serializer):
    id = serializers.CharField()
    phase = serializers.CharField()
    isFreeText = serializers.BooleanField(required=False, default=False)
    freeTextStatement = serializers.CharField(required=False, allow_blank=True, default="")
    # Structured fields — all free-text-capable; never ChoiceField
    canonicalVariable = serializers.CharField(required=False, allow_blank=True, default="")
    subcategory = serializers.CharField(required=False, allow_blank=True, default="")
    operator = serializers.CharField(required=False, allow_blank=True, default="")
    thresholdValue = serializers.CharField(required=False, allow_blank=True, default="")
    thresholdUnit = serializers.CharField(required=False, allow_blank=True, default="")
    probabilityValue = serializers.FloatField(required=False, allow_null=True)
    leadTimeValue = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    timeframeUnit = serializers.CharField(required=False, allow_blank=True, default="days")
    geographyType = serializers.CharField(required=False, allow_blank=True, default="national")
    geographyLabel = serializers.CharField(required=False, allow_blank=True, default="")
    geographyFeatureId = serializers.CharField(required=False, allow_blank=True, default="")
    geographyCoordinates = serializers.DictField(required=False, allow_null=True)
    geographySource = serializers.CharField(required=False, allow_blank=True, default="")
    geographyConfirmed = serializers.BooleanField(required=False, default=False)
    sourceAuthority = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    withinConnector = serializers.CharField(required=False, allow_blank=True, default="")
    crossConnector = serializers.CharField(required=False, allow_blank=True, default="")


class GenerationOptionsSerializer(serializers.Serializer):
    pass


class ValidateRequestSerializer(serializers.Serializer):
    documentContext = DocumentContextSerializer()
    statements = StatementDraftSerializer(many=True)


class GenerateRequestSerializer(serializers.Serializer):
    documentContext = DocumentContextSerializer()
    statements = StatementDraftSerializer(many=True)
    generationOptions = GenerationOptionsSerializer(required=False)


class RegenerateRequestSerializer(serializers.Serializer):
    documentContext = DocumentContextSerializer()
    statements = StatementDraftSerializer(many=True)
    generationOptions = GenerationOptionsSerializer(required=False)
    reviewerNotes = serializers.CharField(required=False, allow_blank=True, default="")


class DeterministicDraftSerializer(serializers.Serializer):
    preActivation = serializers.CharField()
    activation = serializers.CharField()
    stop = serializers.CharField()
    combined = serializers.CharField()


class ReviewOutputSerializer(serializers.Serializer):
    preActivation = serializers.CharField()
    activation = serializers.CharField()
    stop = serializers.CharField()
    combined = serializers.CharField()
    warnings = serializers.ListField(child=serializers.CharField(), required=False)


class ValidateResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    warnings = serializers.ListField(child=serializers.CharField())
    errors = serializers.ListField(child=serializers.CharField())


class GenerateResponseSerializer(serializers.Serializer):
    documentContext = DocumentContextSerializer()
    statements = StatementDraftSerializer(many=True)
    deterministicDraft = DeterministicDraftSerializer()
    reviewOutput = ReviewOutputSerializer()
    warnings = serializers.ListField(child=serializers.CharField())
    modelId = serializers.CharField()
    promptVersion = serializers.CharField()
