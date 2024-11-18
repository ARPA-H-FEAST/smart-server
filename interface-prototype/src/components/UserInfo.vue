<template>
  <v-container>
        <v-card>
            <v-card-title class="text-center">
                Current User Information
            </v-card-title>
            <v-col>
                User: {{ userStore.user }}<br>
                Authenticated: {{ userStore.isAuthenticated }}<br>
                CSRF Token: {{ userStore.token }}<br>
                OAuth2.0 Code: {{ userStore.code }}<br>
                OAuth2.0 Token: {{ userStore?.credentials.accessToken }}<br>
                OAuth2.0 Refresh Token: {{ userStore?.credentials.refreshToken }}<br>
                OIDC ID Token: {{ parseJWT(userStore.credentials)  }}<br>

            </v-col>
        </v-card>
      </v-container>
</template>
<script setup>

import { useUserStore } from '@/stores/user';
import { onMounted } from 'vue';

const userStore = useUserStore()

function _parseJWT(token) {
    const base64URL = token.split('.')[1];
    const base64 = base64URL.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));   
    return JSON.parse(jsonPayload)
}

function parseJWT(credentials) {
  if (!credentials) {
      return "No credentials"
  } else {
    const credentialText = credentials.idToken ? _parseJWT(credentials.idToken) : "OIDC only"
    return credentialText
    }
  }

</script>