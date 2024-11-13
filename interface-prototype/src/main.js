/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'
import router from './router'
import { generatePKCE } from "@/utilities/pkce";

// Composables
import { createApp } from 'vue'
import { createPinia } from 'pinia'

const pinia = createPinia()
const app = createApp(App)

router.onError((error, to) => {
    console.log('---> Router captured error!');
    if (error.message.includes('error loading dynamically imported module') ||
        error.message.includes('Failed to fetch dynamically imported module') || 
        error.message.includes('Importing a module script failed')) {
            window.location = to.fullPath;
    } else {
        console.log('--> Error was %s', error);
    }
})

async function createClientNonces() {
    // Create PKCE requirements just once per session
    // i.e. avoid refresh on remounting userStore
    // requires browser
    await generatePKCE()
    // console.log("Got PKCE Challenge: ", sessionStorage.getItem('code_challenge'))
    // console.log("Got PKCE Verifier: ", sessionStorage.getItem('code_verifier'))
  }

createClientNonces()

app.use(pinia)
app.use(router)

registerPlugins(app)

app.mount('#app')
