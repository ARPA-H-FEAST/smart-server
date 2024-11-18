<template>
    <v-container>
        <v-btn type="submit" @click.prevent="getComplianceStatement()" >FHIR Compliance Statement</v-btn>
    </v-container>
</template>
<script setup>

import { useUserStore } from '@/stores/user';
import { onMounted } from 'vue';

const userStore = useUserStore()

async function getComplianceStatement() {
    
    console.log("Getting response with token ", userStore.credentials.idToken);

    const response = await fetch("http://localhost:8000/smart-feast/api/fhir/", {
        method: 'GET',
        headers: {
            // NB Can use either accessToken (bearer) or idToken (JWT; OIDC flow _only_). 
            'Authorization': 'Bearer ' + userStore?.credentials.idToken,
        }
    })
    if (response.ok) {
        console.log(">>>> Response status is ", response.status)
        if (response.redirected) {
            console.log("---> Got redirect to URL: ", response.url)
        } else {
            const details = await response.json()
            console.log("---> Recieved response ", details)
        }
    }
}


onMounted(() => {
    console.log("Composition: mounted!")
    console.log("---> Store? ", userStore.user)
  }
)

</script>