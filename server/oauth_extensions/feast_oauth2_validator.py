from oauth2_provider.oauth2_validators import OAuth2Validator

class FEASTOAuth2Validator(OAuth2Validator):

    oidc_claim_scope = OAuth2Validator.oidc_claim_scope
    oidc_claim_scope = None

    def get_additional_claims(self, request):
        if request.user is None:
            # An automated system has been authenticated
            if str(request.client) == "FEAST Data Post Application":
                # The authenticated system has permission 
                # to POST information to the database
                return {"client_special_permission": "write"}
            return {}
        else:
            return {}
