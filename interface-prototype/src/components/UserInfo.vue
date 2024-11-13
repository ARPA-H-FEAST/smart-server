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
                OIDC ID Token: {{ userStore?.credentials.idToken  }}<br>

            </v-col>
        </v-card>
      </v-container>
</template>
<script setup>

import { useUserStore } from '@/stores/user';
import { onMounted } from 'vue';

const userStore = useUserStore()


</script>