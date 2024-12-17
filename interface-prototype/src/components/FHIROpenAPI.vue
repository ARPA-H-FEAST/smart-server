<template>
    <v-container>
        <v-text-field 
          hint="Raw Query Text"
          type="input"
          v-model="queryText"        
        >
        </v-text-field>
        <v-btn type="submit" @click.prevent="getFHIROpenAPIResponse()" >FHIR Open API Interface</v-btn>
    </v-container>
</template>
<script setup>

import { useUserStore } from '@/stores/user';
import { onMounted } from 'vue';

const userStore = useUserStore()

async function getFHIROpenAPIResponse() {
    
    const response = await fetch(`http://localhost:8000/smart-feast/api/fhir-openapi/`, {
        method: 'GET',
        headers: {},
    })
    if (response.ok) {
        console.log(">>>> Response status is ", response.status)
        if (response.redirected) {
            console.log("---> Got redirect to URL: ", response.url)
        } else {
            const details = await response.text()
            console.log("---> Recieved response ", details)
        }
    }
}

let queryText = null;
let jsonResponse = null;

onMounted(() => {
    console.log("Composition: mounted!")
    console.log("---> Store? ", userStore.user)
  }
)

</script>