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

app.use(pinia)
app.use(router)

registerPlugins(app)

app.mount('#app')
