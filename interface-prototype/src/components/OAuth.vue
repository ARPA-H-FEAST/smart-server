<template>
    <v-container class="justify-left">
        <v-btn type="submit" @click.prevent="oauthAuthorize()">OAuth: Authorize</v-btn>
        <v-btn type="submit" @click.prevent="oauthGetToken()">OAuth: Obtain Token</v-btn>
    </v-container>
</template>
<script setup>

import { useUserStore } from '@/stores/user';
import { onMounted } from 'vue';

const userStore = useUserStore()

async function oauthAuthorize() {
          const response = await userStore.oauthAuthorize()
          console.log("OAuth: Redirect is ", response)
          if (response) {
            console.log("---> Redirecting router to ", response)
            window.location.replace(response)
          }
        }

async function oauthGetToken() {
    const response = await userStore.oauthGetToken()
    console.log("OAuth: Code exchanged for token")
    if (response) {
        // handle result
    }
}

onMounted(() => {
    console.log("Composition: mounted!")
    console.log("---> Store? ", userStore.user)
  }
)

</script>