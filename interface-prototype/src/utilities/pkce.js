function generateRandomString(length) {
    let result = '';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const charactersLength = characters.length;
    let counter = 0;
    while (counter < length) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
      counter += 1;
    }
    return result;
}

async function generateCodeChallenge(codeVerifier) {
    const data = new TextEncoder().encode(codeVerifier);
    const hash = await crypto.subtle.digest('SHA-256', data);
  
    // Base64 encode the hash, then URL-safe encode it
    return btoa(String.fromCharCode(...new Uint8Array(hash)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
}

function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

export async function generatePKCE() {
  
  if (!sessionStorage.getItem('code_verifier') | !sessionStorage.getItem('code_challenge')){

    const randomizedLength = getRandomInt(43, 128);
    // Generate a random code verifier
    console.log("---> Got randomized length: ", randomizedLength);
    const codeVerifier = generateRandomString(randomizedLength);
    console.log("---> Got a code verifier: ", codeVerifier);

    // Hash the code verifier using SHA-256
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    console.log("---> Got a code challenge: ", codeChallenge);

    // Store the code verifier in session storage
    sessionStorage.setItem('code_verifier', codeVerifier);
    sessionStorage.setItem('code_challenge', codeChallenge)
    return true
  // return { codeVerifier, codeChallenge };
  } else { return true }
}