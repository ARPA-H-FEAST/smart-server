<template>
    <v-container>
        <v-text-field 
          label="Raw Query Text"
          type="input"
          v-model="queryText"
          persistent-hint      
        >
        </v-text-field>
        <v-btn type="submit" @click.submit="getFHIRResponse()" >FHIR query interface</v-btn>
        <v-text-field 
          label="JSON Info for POST"
          type="input"
          v-model="jsonPostInfo"
          persistent-hint      
        >
        </v-text-field>
        <v-btn type="submit" @click.submit="getFHIRPostResponse()" >FHIR POST interface</v-btn>
    </v-container>
    <v-container>
        <v-card variant="flat" :v-if="jsonResponse">
            <v-card-text>
                {{ jsonResponse }}
            </v-card-text>
        </v-card>
        {{ queryText }}
    </v-container>
</template>
<script setup>

import { useUserStore } from '@/stores/user';
import { ref, onMounted } from 'vue';

const userStore = useUserStore()

async function getFHIRResponse() {
    
    this.jsonResponse = null;

    const response = await fetch(`http://localhost:8000/smart-feast/api/query/?q=${queryText.value}`, {
        method: 'GET',
        headers: {
            "Authorization": "Bearer " + userStore.credentials.idToken
        },
    })
    if (response.ok) {
        console.log(">>>> Response status is ", response.status)
        if (response.redirected) {
            console.log("---> Got redirect to URL: ", response.url)
        } else {
            const details = await response.text()
            // console.log("---> Recieved response ", details)
            this.jsonResponse = JSON.parse(details)
        }
    }
}

async function getFHIRPostResponse() {
    
    this.jsonResponse = null;

    const response = await fetch(`http://localhost:8000/smart-feast/api/query/?q=${queryText.value}`, {
        method: 'POST',
        credentials: "include",
        headers: {
            "X-CSRFToken": userStore.token,
            "Authorization": "Bearer " + userStore.credentials.idToken,
        },
        body: this.jsonPostInfo
    })
    if (response.ok) {
        console.log(">>>> Response status is ", response.status)
        if (response.redirected) {
            console.log("---> Got redirect to URL: ", response.url)
        } else {
            const details = await response.text()
            // console.log("---> Recieved response ", details)
            this.jsonResponse = JSON.parse(details)
        }
    }
}

const queryText = ref("");
const jsonResponse = ref(null);

const jsonPostInfo = ref(null);

onMounted(() => {
    console.log("Composition: mounted!")
    console.log("---> Store? ", userStore.user)
  }
)

</script>