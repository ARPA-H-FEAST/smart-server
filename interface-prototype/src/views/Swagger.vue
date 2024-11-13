<template>

    <v-btn @click.prevent="goToSwagger()">
        Interact with FHIR
    </v-btn>

</template>

<script setup>
import { useUserStore } from '@/stores/user';


const userStore = useUserStore();

async function goToSwagger() {
    // window.location.replace("http://localhost:8080/fhir/swagger-ui/")
    console.log("...Negotiating access to FHIR resources")
    const response = await fetch("http://localhost:8080/fhir/swagger-ui/", {
        method: "GET",
        headers: { "Authorization": "admin" },
        // headers: { "Authorization": "Bearer " + userStore?.credentials.accessToken },
        // credentials: 'include',
    })
    if (!response.ok) {
        // Error handling
        console.log("Caught an error. Le sigh")
    } else {
        // Probably will never get here .... More sighs.
    }
}

</script>
