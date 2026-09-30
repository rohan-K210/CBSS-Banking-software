/**
 * CBSS API Layer — Centralized fetch wrapper for all backend endpoints.
 */

const API_BASE_URL = '';

async function apiRequest(method, url, body = null) {
    const config = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) config.body = JSON.stringify(body);
    const response = await fetch(API_BASE_URL + url, config);
    const data = await response.json();
    if (!response.ok || !data.success) {
        const msg = data.error?.message || `HTTP ${response.status}`;
        throw new Error(msg);
    }
    return data;
}

const AdminAPI = {
    // Stats & data
    getStats:      ()        => apiRequest('GET',  '/api/stats'),
    getCustomers:  ()        => apiRequest('GET',  '/api/customers'),
    getCustomer:   (id)      => apiRequest('GET',  `/api/customers/${id}`),
    getEmployees:  ()        => apiRequest('GET',  '/api/employees'),
    getEmployee:   (id)      => apiRequest('GET',  `/api/employees/${id}`),
    getTransactions: ()      => apiRequest('GET',  '/api/transactions'),

    // Customer CRUD
    addCustomer:   (data)    => apiRequest('POST', '/api/customers/add', data),
    editCustomer:  (data)    => apiRequest('POST', '/api/customers/edit', data),
    deleteCustomer:(data)    => apiRequest('POST', '/api/customers/delete', data),
    searchCustomer:(data)    => apiRequest('POST', '/api/customers/search', data),

    // Employee CRUD
    addEmployee:   (data)    => apiRequest('POST', '/api/employees/add', data),
    editEmployee:  (data)    => apiRequest('POST', '/api/employees/edit', data),
    deleteEmployee:(data)    => apiRequest('POST', '/api/employees/delete', data),
    searchEmployee:(data)    => apiRequest('POST', '/api/employees/search', data),

    // Loan evaluation
    evaluateLoan:  (data)    => apiRequest('POST', '/api/loan/evaluate', data),

    // Segmentation
    predictSegment:(data)    => apiRequest('POST', '/api/segmentation/predict', data),

    // Fraud
    getPendingFraud: ()      => apiRequest('GET',  '/api/fraud/pending'),
    decideFraud:    (data)   => apiRequest('POST', '/api/fraud/decide', data),
};
