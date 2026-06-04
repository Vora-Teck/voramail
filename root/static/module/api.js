// api.js
import * as IDB from "./idb-keys.js";

export const BASE_URL = ``;



// User Info (now in IndexedDB meta store)
export async function saveUserInfo(obj) { return IDB.setMeta("user_info", obj); }
export async function getUserInfo() { return IDB.getMeta("user_info"); }
export async function clearUserInfo() { return IDB.delMeta("user_info"); }


export async function getKey(name) { return IDB.getKey(name); }
export async function setKey(name, value) { return IDB.putKey(name, value); }
export async function clearKey(name) { return IDB.deleteKey(name); }



const buildQueryString = (params = {}) => {
  const query = new URLSearchParams();

  for (const key in params) {
    if (Array.isArray(params[key])) {
      params[key].forEach((val) => query.append(key, val));
    } else {
      query.append(key, params[key]);
    }
  }

  return query.toString() ? `?${query.toString()}` : '';
};


const request = async ({ method = 'GET', url, data = null, params = {}}) => {
  const queryString = buildQueryString(params);
  const fullUrl = `${BASE_URL}${url}${queryString}`;

  const access_token = await getKey("access_token");
  const refresh_token = await getKey("refresh_token");

  if((!access_token || !refresh_token) && location.pathname !== "/login") {
    location.href = "/login";
    return;
  }

  const isFormData = data instanceof FormData;

  const headers = {
    //...({ 'Accept': 'application/json' }),
    ...(!isFormData && { 'Content-Type': 'application/json' }),
    ...(access_token && {'Authorization': `Bearer ${access_token}`})
  };

  //console.log(headers)

  const options = {
    method: method.toUpperCase(),
    headers,
  };

  if (method !== 'GET' && method !== 'HEAD' && data) {
    options.body = isFormData ? data : JSON.stringify(data);
  }
  try {
    let response = await fetch(fullUrl, options);
    
    // If access token expired
    if (response.status === 401) {
    
      // Try refresh
      const refresh = await fetch(`/auth/refresh`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${refresh_token}`
        }
      });
      //console.log(refresh, refresh.status)
    
      if (refresh.status !== 200) {
        // refresh token expired → logout user
        await clearKey("access_token")
        await clearKey("refresh_token")
        window.location.href = "/login";
        return;
      }

      const refresh_data = await refresh.json()
      await setKey("access_token", refresh_data['access_token'])

      options.headers['Authorization'] = `Bearer ${refresh_data['access_token']}`

      // retry original request
      response = await fetch(fullUrl, options);
    }

    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    const responseData = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      responseData['statusText'] = response.statusText;
      responseData['statusCode'] = response.status;
      return responseData;
    }

    return responseData;
  }
  catch (error) {
    throw error;
  }
};



// authentication endpoints
export async function register(payload) {
  return await request({ method: 'POST', url: "/auth/register", data: payload }) 
}
export async function login(payload) {
  return await request({ method: 'POST', url: "/auth/login", data: payload }) 
}
export async function logout() {
  return await request({ method: 'POST', url: "/auth/logout" }) 
}
export async function getApiKeys() {
  return await request({ method: 'GET', url: "/auth/rotate-keys" }) 
}

// profile endpoints
export async function userProfile() {
  return await request({ method: 'GET', url: "/me" }) 
}
export async function userKPI() {
  return await request({ method: 'GET', url: "/me/kpi" }) 
}


// Settings endpoints
export async function publicKey() {
  return await request({ method: 'GET', url: "/me/api-key" }) 
}
export async function webhookData() {
  return await request({ method: 'GET', url: "/me/webhook" }) 
}
export async function generateKey() {
  return await request({ method: 'POST', url: "/auth/rotate-keys", data: {} }) 
}
export async function saveWebhookData(payload) {
  return await request({ method: 'POST', url: "/me/webhook", data: payload }) 
}
export async function updatePassword(payload) {
  return await request({ method: 'POST', url: "/me/change-password", data: payload }) 
}

// Agent endpoints
export async function getAccounts() {
  return await request({ method: 'GET', url: "/accounts" }) 
}
export async function createAccount(payload) {
  return await request({ method: 'POST', url: "/accounts", data: payload }) 
}
export async function getAccount(id) {
  return await request({ method: 'GET', url: `/accounts/${id}` }) 
}
export async function updateAccount(id, payload) {
  return await request({ method: 'POST', url: `/accounts/${id}`, data: payload }) 
}
export async function deleteAccount(id) {
  return await request({ method: 'DELETE', url: `/accounts/${id}` }) 
}
export async function getMails(id, params) {
  return await request({ method: 'GET', url: `/accounts/${id}/mails`, params: params }) 
}
export async function getMail(mail_id) {
  return await request({ method: 'GET', url: `/accounts/mails/${mail_id}` }) 
}



