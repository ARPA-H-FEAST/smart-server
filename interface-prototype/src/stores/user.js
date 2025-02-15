import { defineStore } from "pinia";

import { getCookie } from "@/utilities/cookies";

export const useUserStore = defineStore("user", {
  state: () => ({
    user: null,
    token: null,
    isAdmin: false,
    role: 0,
    isAuthenticated: false,
    error: null,
    targetURL: import.meta.env.DEV ? import.meta.env.VITE_DEV_MIDDLEWARE_BASE + '/smart-feast' : '/smart-feast',
    oauthURL: import.meta.env.DEV ? import.meta.env.VITE_DEV_MIDDLEWARE_BASE + '/smart-feast/oauth' : '/smart-feast/oauth',
    credentials: {},
    code: null,
    oauth: {
      response_code: "code",
      code_challenge_method: "S256",
      client_id: "KEKIrAVQCOZKkCmfyAiWy8qAe0BvQaNYhV1HUuXx",
      redirect_uri: "http://localhost:3000/callback/",
    },
    oidc: {
      response_code: "code",
      code_challenge_method: "S256",
      client_id: "uaAfDJyuoLo6d32XGYGawtLsWGlsJvGdDs3sENTm",
      redirect_uri: "http://localhost:3000/callback/",
    }
}),

  mounted() {
    // Update the CSRF token when the store has been remounted
    //  (eg, the page has been refreshed)
    this.checkUser();
    },
  actions: {

    clearError() {
      this.error = null;
    },

    handleUserResponse(response) {
      console.log("Handling response: %s", JSON.stringify(response));
      if (response.error) {
        this.error = response.error;
        return false;
      }

      if (response.detail) {
        this.error = response.detail;
        return false;
      }

      if (response.created || response.update) {
        console.log("Found a user creation / update");
        // No updates, but operation was successful
        return true;
      };
      
      if (response.admin) {
        console.log("Confirming admin access ....");
        this.isAdmin = true;
      } else {
        this.isAdmin = false
      };

      if (response.role) {
        console.log("Confirming role presence: ", response.role);
        switch(response.role) {
          case "Backend":
            this.role = 5; break;
          case "Administrator":
            this.role = 4; break;
          case "Researcher":
            this.role = 3; break;
          case "Clinician":
            this.role = 2; break;
          case "Patient":
            this.role = 1; break;
          default:
            console.log("===> ERROR on role: Fond value ", response.role);
        }
      };

      if (response.isAuthenticated) {
        this.isAuthenticated = true;
      } else {
        this.isAuthenticated = false;
      }

      if (!response.email) {
        console.log("Got a response non-username: %s", response.email);
        this.user = null;
        this.token = null;
        return false;
      }
      this.user = response['email'];
      this.token = getCookie('csrftoken');
      return true;
    },

    async login(email, password) {
      const res = await fetch(`${this.targetURL}/login/`, {
        method: "POST",
        // credentials: "same-origin",
        credentials: "include",
        headers: {
          "Accept": 'application/json',
          // "Content-Type": "application/json",
          // "X-CSRFToken": this.token,
        },
        body: JSON.stringify({ email, password }),
      });
    
      if (!res.ok) {
        // Error handling
      }

      const response = await res.json();

      if (!response){
        // Error handling
      }

      const success = this.handleUserResponse(response);
      if (!success) {
        console.log("Error on login - response was %s", JSON.stringify(response));
      }
      return success;
    },

    async logout() {
      // console.log('->>> Attempting to log out!');
      // const response = this.fetchHelper("/logout", true);
      if (!this.user && !this.token) {
        this.user = null; 
        this.token = null;
        return true;
      }
      const res = await fetch(`${this.targetURL}/logout/`, {
        // method: "POST",  
        credentials: "include",
        // credentials: "same-origin",
        headers: {
          "Accept": 'application/json',
          // "Content-Type": "application/json",
          // "X-CSRFToken": this.token,
        },
      })
      if (!res.ok) {
        // Error handling
      }

      const response = await res.json();
      var success = this.handleUserResponse(response);
      // success should be false on logout
      success = !success;
      if (!success) {
        console.log("Error in logout - see logs")
      }
      this.user = null;
      this.token = null;
      this.code = null;
      this.credentials = {};
      this.isAdmin = false;
      this.isAuthenticated = false;

      console.log("User store state is now: User %s Token %s", this.user, this.token);

      return success;
    },

    async checkUser() {
      // console.log("=>>> User record: %s", this.user);
      const res = await fetch(`${this.targetURL}/whoami/`, {
        // credentials: "same-origin",
        credentials: "include",
        headers: {
          "Accept": "application/json",
          // "X-CSRFToken": this.token,
        }
      })
      if (!res.ok) {
        /// Error handling
      }
      const response = await res.json();

      console.log("---> WhoAmI reported: %s", JSON.stringify(response));
      
      const success = this.handleUserResponse(response);
      if (!success){
        // Error handling. NB: Users not yet logged in will
        // return `false`y from handleUserResponse.
        // console.log("Error on checking user through `whoami`");
      }

      return success;

    },

    
    async oauthAuthorize(){

      // const res = await fetch(
      //   `${this.oauthURL}/authorize/?response_type=${this.oauth.response_code}&code_challenge=${this.oauth.code_challenge}&code_challenge_method=${this.oauth.code_challenge_method}&client_id=${this.oauth.client_id}&redirect_uri=${this.oauth.redirect_uri}`
      // )
      const code_challenge = sessionStorage.getItem('code_challenge')
      const code_verifier = sessionStorage.getItem('code_verifier')
      const res = await fetch(
        `${this.oauthURL}/authorize/?response_type=${this.oauth.response_code}&code_challenge=${code_challenge}&code_challenge_method=${this.oauth.code_challenge_method}&code_verifier=${code_verifier}&client_id=${this.oauth.client_id}&redirect_uri=${this.oauth.redirect_uri}`
      )
      // const response = await res.json()

      // console.log("Got response: ", res)
      if (res.url) {
        const url = new URL(res.url)
        // const urlString = 
        console.log("Found URL: ", url.searchParams.get('next'))
        return url.searchParams.get('next')
      }
      return null
    },

    async oidcAuthorize(){

      // const pkceObj = await generatePKCE()
      const code_challenge = sessionStorage.getItem('code_challenge')
      const code_verifier = sessionStorage.getItem('code_verifier')
      // console.log("Got Code Challenge: ", code_challenge)
      // console.log("Got Code verifier: ", code_verifier)

      // this.oidc.code_challenge = pkceObj.code_challenge
      // this.oidc.code_verifier = pkceObj.code_verifier

      const res = await fetch(
        `${this.oauthURL}/authorize/?response_type=${this.oidc.response_code}&code_challenge=${code_challenge}&code_challenge_method=${this.oidc.code_challenge_method}&code_challenge=${code_challenge}&client_id=${this.oidc.client_id}&redirect_uri=${this.oidc.redirect_uri}`
      )
      // const response = await res.json()

      console.log("Got response: ", res)
      if (res.url) {
        const url = new URL(res.url)
        // const urlString = 
        console.log("Found URL: ", url.searchParams.get('next'))
        return url.searchParams.get('next')
      }
      return null
    },

    async oauthGetToken() {

      const code_verifier = sessionStorage.getItem('code_verifier')

      // Great walkthrough on SO: https://stackoverflow.com/a/35553666
      // ...not sure it solves my issue
      const headers = new Headers({
        "Cache-Control": "no-cache",
        // Note that requests routed to oauthlib.oauth2.rfc6749.endpoints.token_endpoint.create_token_response
        // arrive as raw `x-www-form-urlencoded` (i.e., are need decoded correctly by receiving sink)
        // Using `urllib.parse.unquote(requst.body)` results in a slightly-mangled JSON string. 
        // ...chalking this up as a bug in Python library for now
        // "Content-Type": "application/x-www-form-urlencoded",
        "Content-Type": "application/json",
      })
        console.log("OAuth: Getting token, with code %s and verifier\n%s", this.code, this.code_verifier)
        const res = await fetch(
          `${this.oauthURL}/token/`,
          {
            headers: headers,
            method: 'POST',
            body: JSON.stringify(
              {
                client_id: this.oauth.client_id,
                // client_secret: this.oauth.client_secret,
                code: this.code,
                code_verifier: code_verifier,
                redirect_uri: this.oauth.redirect_uri,
                grant_type: 'authorization_code',
              })
          }
      ) 
      // console.log("Get Token: Got response ", res)
      const response = await res.json()
      // console.log("Get Token: Unrolled ", response)
      this.credentials = {
        accessToken: response.access_token,
        tokenType: response.token_type,
        scope: response.scope,
        refreshToken: response.refresh_token,
        idToken: response.id_token ? response.id_token : "OIDC only",
      }
      this.code = null
      console.log("New credentials: ", JSON.stringify(this.credentials))

    },

    async oidcGetToken() {

      const code_verifier = sessionStorage.getItem('code_verifier')

      // Great walkthrough on SO: https://stackoverflow.com/a/35553666
      // ...not sure it solves my issue
      const headers = new Headers({
        "Cache-Control": "no-cache",
        // Note that requests routed to oauthlib.oauth2.rfc6749.endpoints.token_endpoint.create_token_response
        // arrive as raw `x-www-form-urlencoded` (i.e., are need decoded correctly by receiving sink)
        // Using `urllib.parse.unquote(requst.body)` results in a slightly-mangled JSON string. 
        // ...chalking this up as a bug in Python library for now
        // "Content-Type": "application/x-www-form-urlencoded",
        "Content-Type": "application/json",
      })
        console.log("OIDC: Getting token, with code %s and verifier\n%s", this.code, code_verifier)
        const res = await fetch(
          `${this.oauthURL}/token/`,
          {
            headers: headers,
            method: 'POST',
            body: JSON.stringify(
              {
                client_id: this.oidc.client_id,
                code: this.code,
                code_verifier: code_verifier,
                redirect_uri: this.oidc.redirect_uri,
                grant_type: 'authorization_code',
              })
          }
      ) 
      console.log("Get Token: Got response ", res)
      const response = await res.json()
      console.log("Get Token: Unrolled ", response)
      this.credentials = {
        accessToken: response.access_token,
        tokenType: response.token_type,
        scope: response.scope,
        refreshToken: response.refresh_token,
        idToken: response.id_token ? response.id_token : "OIDC only",
      }
      this.code = null
      console.log("New credentials: ", JSON.stringify(this.credentials))

    },

    async createUser(email, password, firstName, lastName, userRole) {
      // console.log("--> Attempting to register user with credentials:\nUser %s Password: %s\n Name: %s %s\nRole", email, password, firstName, lastName, userRole);

      const res = await fetch(`${this.targetURL}/create-user/`, {
        method: "POST",
        // credentials: "same-origin",
        // credentials: "include",
        // mode: "cross-origin",
        headers: {
          "Accept": "application/json",
          // "X-CSRFToken": this.token,
        },
        body: JSON.stringify(
          {
            "first_name": firstName,
            "last_name": lastName,
            "email": email,
            "password": password,
            "category": userRole,
          }
        )
      })

      if (!res.ok) {
        // Error handling
      }

      const response = await res.json();

      const success = this.handleUserResponse(response);
      if (!success) {
        console.log("Error on user creation - See logs");
      }
      return success;
    },

    async updateProfile(userID, firstName, lastName, password, email) {
    console.log("Current CSRF token: %s", this.token);
    const res = await fetch(`${this.targetURL}/update-user/`, {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": this.token,
      },
      body: JSON.stringify({
        "first_name": firstName,
        "last_name": lastName,
        "password": password,
        "email": email,
        "user_id": userID,
      })
    })

    if (!res.ok) {
      // Error handling
    }
    const response = await res.json();
    const success = this.handleUserResponse(response);
    if (!success) {
      // Error handling
    }
    return success;
  },

  async updatePassword(userID, oldPassword, newPassword) {
    this.error = null;
    const res = await fetch(`${this.targetURL}/update-user/`, {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": this.token,
      },
      body: JSON.stringify({
        "old_password": oldPassword,
        "new_password": newPassword,
        "user_id": userID,
      })
    })

    if (!res.ok) {
      // Error handling
    }

    const response = await res.json();

    const success = this.handleUserResponse(response);
    if (!success) {
      // Error handling
    }
    return success;
  },

  async deleteUser(userID) {
    this.error = null;
    const res = await fetch(`${this.targetURL}/delete-user/`, {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": this.token,
      },
      body: JSON.stringify({
        "user_id": userID,
      })
    })

    if (!res.ok) {
      // Error handling
      console.log("User deletion: Result not OK!");
    }

    const response = await res.json();

    var success = this.handleUserResponse(response);
    // success should be false on deletion
    success = !success;
    if (!success) {
      // Error handling
    }
    console.log("User store: Deletion final report: %s", success);
    return success;
  },
  }
});
