// QuickKart Application JavaScript

// Application state
let currentPage = 'home';
let searchResults = [];
let locationData = {
    address: 'Detecting location...',
    latitude: null,
    longitude: null,
    pincode: null
};

// Platform metadata
const PLATFORM_META = {
    blinkit: { name: "Blinkit", color: "bg-yellow-500", logo: "static/assets/Blinkit_logo.webp" },
    zepto: { name: "Zepto", color: "bg-purple-500", logo: "static/assets/zepto_logo.webp" },
    dmart: { name: "DMart", color: "bg-green-500", logo: "static/assets/Dmart_logo.webp" }
};

// DOM elements
const elements = {
    homePage: document.getElementById('home-page'),
    loadingPage: document.getElementById('loading-page'),
    resultsPage: document.getElementById('results-page'),
    locationModal: document.getElementById('location-modal'),
    searchModal: document.getElementById('search-modal'),
    mainSearch: document.getElementById('main-search'),
    userLocation: document.getElementById('user-location'),
    recentList: document.getElementById('recent-list'),
    resultsGrid: document.getElementById('results-grid'),
    resultsQuery: document.getElementById('results-query')
};

// Location caching functions
function saveLocationToCache() {
    try {
        const locationToSave = {
            address: locationData.address,
            latitude: locationData.latitude,
            longitude: locationData.longitude,
            pincode: locationData.pincode,
            timestamp: Date.now()
        };
        localStorage.setItem('quickkart_location', JSON.stringify(locationToSave));
    } catch (error) {
        console.error('Failed to save location to cache:', error);
    }
}

function loadLocationFromCache() {
    try {
        const cached = localStorage.getItem('quickkart_location');
        if (cached) {
            const locationCache = JSON.parse(cached);
            const cacheAge = Date.now() - (locationCache.timestamp || 0);
            const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days

            if (cacheAge < maxAge && locationCache.latitude && locationCache.longitude) {
                locationData.address = locationCache.address || 'Cached location';
                locationData.latitude = locationCache.latitude;
                locationData.longitude = locationCache.longitude;
                locationData.pincode = locationCache.pincode;
                return true;
            }
        }
    } catch (error) {
        console.error('Failed to load location from cache:', error);
    }
    return false;
}

function clearLocationCache() {
    try {
        localStorage.removeItem('quickkart_location');
    } catch (error) {
        console.error('Failed to clear location cache:', error);
    }
}

// Page management
function showPage(page) {
    elements.homePage.classList.add('hidden');
    elements.loadingPage.classList.add('hidden');
    elements.resultsPage.classList.add('hidden');

    switch (page) {
        case 'home':
            elements.homePage.classList.remove('hidden');
            break;
        case 'loading':
            elements.loadingPage.classList.remove('hidden');
            startLoadingAnimation();
            break;
        case 'results':
            elements.resultsPage.classList.remove('hidden');
            break;
    }
    currentPage = page;
}

// Modal management
function openLocationModal() {
    elements.locationModal.classList.remove('hidden');
    const locationInput = document.getElementById('location-search');
    locationInput.value = '';
    locationInput.focus();

    // Initialize Google Places if not already done
    if (!placesAutocomplete) {
        initializeGooglePlaces();
        placesAutocomplete = true; // Mark as initialized
    }
}

function closeLocationModal() {
    elements.locationModal.classList.add('hidden');
}

function openSearchModal() {
    elements.searchModal.classList.remove('hidden');
    document.getElementById('search-input').focus();
    populateSearchSuggestions();
}

function closeSearchModal() {
    elements.searchModal.classList.add('hidden');
}

// Search functionality
async function performSearch(query) {
    if (!query.trim()) return;

    addToRecent(query);
    elements.resultsQuery.textContent = `"${query}"`;
    showPage('loading');

    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                ...locationData
            })
        });

        if (response.ok) {
            searchResults = await response.json();
        } else {
            throw new Error('Search failed');
        }
    } catch (error) {
        console.error('Search error:', error);
        searchResults = [];
    }

    setTimeout(() => {
        lastResults = searchResults;
        activePlatform = 'all';
        renderResults(searchResults);
        filterPlatform('all');
        showPage('results');
    }, 2000);
}

// Recent searches
function addToRecent(query) {
    let recent = JSON.parse(localStorage.getItem('recent_searches') || '[]');
    recent = recent.filter(item => item !== query);
    recent.unshift(query);
    recent = recent.slice(0, 5);
    localStorage.setItem('recent_searches', JSON.stringify(recent));
    renderRecentSearches();
}

function renderRecentSearches() {
    const recent = JSON.parse(localStorage.getItem('recent_searches') || '[]');
    elements.recentList.innerHTML = recent.map(query => `
        <div class="recent-chip cursor-pointer hover:opacity-80 transition-opacity" data-query="${query}">
            <svg class="w-4 h-4" style="color: var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 110-15 7.5 7.5 0 010 15z"></path>
            </svg>
            <span>${query}</span>
            <button class="remove-recent ml-2 hover:opacity-80" style="color: var(--text-tertiary)" data-query="${query}">×</button>
        </div>
    `).join('');
}

// Search suggestions
function populateSearchSuggestions(query = '') {
    const suggestions = generateSmartSuggestions(query);

    if (suggestions.length === 0) {
        document.getElementById('search-suggestions').innerHTML = `
            <div class="p-6 text-center" style="color: var(--text-tertiary)">
                <svg class="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 110-15 7.5 7.5 0 010 15z"></path>
                </svg>
                <div class="text-sm">${query ? 'No matching suggestions found.' : 'Start typing to see suggestions'}</div>
            </div>
        `;
        return;
    }

    document.getElementById('search-suggestions').innerHTML = suggestions.map(suggestion => `
        <div class="search-suggestion p-4 rounded-lg cursor-pointer flex items-center gap-3 hover:opacity-80 transition-opacity" data-query="${suggestion}">
            <svg class="w-5 h-5" style="color: var(--text-secondary)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 110-15 7.5 7.5 0 010 15z"></path>
            </svg>
            <div class="flex-1">
                <span style="color: var(--text-primary)">${suggestion}</span>
            </div>
        </div>
    `).join('');
}

function generateSmartSuggestions(query) {
    const staticSuggestions = [
        "Atta", "Rice", "Detergent", "Coffee", "Milk", "Bread",
        "Eggs", "Oil", "Sugar", "Tea", "Biscuits", "Soap"
    ];

    if (!query || query.trim().length === 0) {
        return staticSuggestions.slice(0, 6);
    }

    const queryLower = query.toLowerCase().trim();
    return staticSuggestions.filter(item =>
        item.toLowerCase().includes(queryLower)
    ).slice(0, 8);
}

// Google Places functionality
let placesAutocomplete = null;

function initializeGooglePlaces() {
    if (window.google && google.maps && google.maps.places) {
        const autocompleteService = new google.maps.places.AutocompleteService();

        // Handle location search input
        const locationInput = document.getElementById('location-search');
        let searchTimeout;

        locationInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            // Clear previous timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }

            if (query.length > 2) {
                // Debounce the search
                searchTimeout = setTimeout(() => {
                    searchPlaces(query);
                }, 300);
            } else {
                clearLocationSuggestions();
            }
        });
    }
}

function searchPlaces(query) {
    if (window.google && google.maps && google.maps.places) {
        const autocompleteService = new google.maps.places.AutocompleteService();

        autocompleteService.getPlacePredictions({
            input: query,
            componentRestrictions: { country: 'IN' },
            types: ['geocode']
        }, (predictions, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK && predictions) {
                displayLocationSuggestions(predictions);
            } else {
                clearLocationSuggestions();
            }
        });
    }
}

function displayLocationSuggestions(predictions) {
    const suggestionsContainer = document.getElementById('location-suggestions');
    suggestionsContainer.innerHTML = predictions.slice(0, 5).map(prediction => `
        <div class="location-suggestion p-4 rounded-lg cursor-pointer hover:opacity-80 transition-opacity" 
             data-place-id="${prediction.place_id}">
            <div class="font-medium" style="color: var(--text-primary)">${prediction.structured_formatting.main_text}</div>
            <div class="text-sm" style="color: var(--text-secondary)">${prediction.structured_formatting.secondary_text || ''}</div>
        </div>
    `).join('');
}

function clearLocationSuggestions() {
    document.getElementById('location-suggestions').innerHTML = '';
}

function selectLocationFromPlaceId(placeId) {
    if (window.google && google.maps && google.maps.places) {
        const placesService = new google.maps.places.PlacesService(document.createElement('div'));

        placesService.getDetails({
            placeId: placeId,
            fields: ['address_components', 'formatted_address', 'geometry']
        }, (place, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK && place) {
                updateLocationFromPlace(place);
                closeLocationModal();
            }
        });
    }
}

function updateLocationFromPlace(place) {
    locationData.latitude = place.geometry.location.lat();
    locationData.longitude = place.geometry.location.lng();
    locationData.address = place.formatted_address;

    // Extract pincode
    const addressComponents = place.address_components || [];
    const pincodeComponent = addressComponents.find(component =>
        component.types.includes('postal_code')
    );
    locationData.pincode = pincodeComponent ? pincodeComponent.long_name : '';

    updateLocationDisplay();
}

// Location functionality
function detectCurrentLocation() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by this browser.');
        return;
    }

    elements.userLocation.textContent = '📍 Detecting location...';

    navigator.geolocation.getCurrentPosition(
        (position) => {
            locationData.latitude = position.coords.latitude;
            locationData.longitude = position.coords.longitude;

            if (window.google && google.maps) {
                const geocoder = new google.maps.Geocoder();
                const latlng = {
                    lat: locationData.latitude,
                    lng: locationData.longitude
                };

                geocoder.geocode({ location: latlng }, (results, status) => {
                    if (status === 'OK' && results[0]) {
                        locationData.address = results[0].formatted_address;
                        const addressComponents = results[0].address_components || [];
                        const pincodeComponent = addressComponents.find(component =>
                            component.types.includes('postal_code')
                        );
                        locationData.pincode = pincodeComponent ? pincodeComponent.long_name : '';
                        updateLocationDisplay();
                    } else {
                        locationData.address = 'Location detected';
                        updateLocationDisplay();
                    }
                });
            } else {
                locationData.address = 'Location detected';
                updateLocationDisplay();
            }
        },
        (error) => {
            console.error('Geolocation error:', error);
            locationData.address = 'Kothrud, Pune (Default)';
            locationData.latitude = 18.5204;
            locationData.longitude = 73.8567;
            locationData.pincode = '411038';
            updateLocationDisplay();
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
}

function updateLocationDisplay() {
    elements.userLocation.textContent = locationData.address;
    saveLocationToCache();
    fetchETAs();
}

// ETA functionality
function formatETA(eta, platformName) {
    if (!eta || eta === 'N/A') {
        return 'Unavailable';
    }

    if (platformName === 'dmart') {
        if (eta.toLowerCase().includes('tomorrow')) {
            const timeMatch = eta.match(/(\d{1,2}):(\d{2})\s*([AP]M)\s*-\s*(\d{1,2}):(\d{2})\s*([AP]M)/i);
            if (timeMatch) {
                const startHour = timeMatch[1];
                const endHour = timeMatch[4];
                const endPeriod = timeMatch[6];
                return `Tomorrow\n${startHour} to ${endHour} ${endPeriod}`;
            }
            return 'Tomorrow';
        }

        if (eta.toLowerCase().includes('today')) {
            const timeMatch = eta.match(/(\d{1,2}):(\d{2})\s*([AP]M)\s*-\s*(\d{1,2}):(\d{2})\s*([AP]M)/i);
            if (timeMatch) {
                const startHour = timeMatch[1];
                const endHour = timeMatch[4];
                const endPeriod = timeMatch[6];
                return `Today\n${startHour} to ${endHour} ${endPeriod}`;
            }
            return 'Today';
        }
    }

    return eta;
}

async function fetchETAs() {
    if (!locationData.latitude || !locationData.longitude) {
        return;
    }

    // Set loading state for all pills
    document.getElementById('eta-blinkit').textContent = 'Loading...';
    document.getElementById('eta-zepto').textContent = 'Loading...';
    document.getElementById('eta-dmart').textContent = 'Loading...';

    // Fetch each ETA individually for real-time updates
    const platforms = [
        { id: 'eta-blinkit', platform: 'blinkit', endpoint: '/eta/blinkit' },
        { id: 'eta-zepto', platform: 'zepto', endpoint: '/eta/zepto' },
        { id: 'eta-dmart', platform: 'dmart', endpoint: '/eta/dmart' }
    ];

    // Fetch each ETA independently - they update as they complete (better UX)
    Promise.all(platforms.map(async ({ id, platform, endpoint }) => {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(locationData)
            });

            if (response.ok) {
                const data = await response.json();
                const eta = data.eta || data[platform] || 'N/A';
                document.getElementById(id).textContent = formatETA(eta, platform);
            } else {
                throw new Error(`${platform} ETA fetch failed`);
            }
        } catch (error) {
            console.error(`${platform} ETA fetch error:`, error);
            document.getElementById(id).textContent = formatETA(null, platform);
        }
    }));
}

// Results rendering
function renderResults(results) {
    if (!results || results.length === 0) {
        elements.resultsGrid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg class="w-16 h-16 mx-auto mb-4" style="color: var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2 2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-2.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 009.586 13H7"></path>
                </svg>
                <p class="text-lg" style="color: var(--text-tertiary)">No products found</p>
                <p class="text-sm mt-2" style="color: var(--text-tertiary)">Try a different search term</p>
            </div>
        `;
        return;
    }

    elements.resultsGrid.innerHTML = results.map(product => {
        const img = product.image_url
            ? `<img src="${product.image_url}" alt="${product.name}" class="h-32 w-auto object-contain mx-auto" onerror="this.style.display='none';" />`
            : `<div class="h-32 w-32 rounded-lg mx-auto flex items-center justify-center" style="background-color: var(--bg-secondary)">
                 <svg class="w-8 h-8" style="color: var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                 </svg>
               </div>`;

        const name = product.name || "Unnamed Product";
        const quantity = product.quantity || "N/A";

        const prices = (product.platforms || []).map(p => {
            const priceStr = p.price || "0";
            const numericPrice = parseFloat(priceStr.replace(/[^\d.]/g, ''));
            return { ...p, numericPrice };
        }).filter(p => p.numericPrice > 0);

        const cheapestPrice = prices.length > 0 ? Math.min(...prices.map(p => p.numericPrice)) : 0;

        const platformRows = (product.platforms || []).map(p => {
            const key = (p.platform || "").toLowerCase();
            const meta = PLATFORM_META[key] || { name: p.platform, color: "bg-gray-500" };
            const price = p.price || "N/A";
            const numericPrice = parseFloat((p.price || "0").replace(/[^\d.]/g, ''));
            const isCheapest = numericPrice > 0 && numericPrice === cheapestPrice;

            let eta = "N/A";
            if (key === "blinkit") {
                eta = document.getElementById("eta-blinkit")?.textContent || "N/A";
            } else if (key === "zepto") {
                eta = document.getElementById("eta-zepto")?.textContent || "N/A";
            } else if (key === "dmart") {
                eta = document.getElementById("eta-dmart")?.textContent || "N/A";
            }

            const stockStatus = p.in_stock !== false ? "" : `<span class="ml-2 text-xs text-red-400">Out of Stock</span>`;
            const priceColor = isCheapest ? "text-green-400 font-bold" : "font-semibold";

            return `
                <a href="${p.product_url || "#"}" target="_blank" rel="noopener noreferrer"
                   class="flex justify-between items-center rounded-lg px-3 py-3 border hover:opacity-80 transition-opacity"
                   style="background-color: var(--bg-elevated); border-color: var(--border-primary)">
                    <div class="flex items-center gap-2">
                        <div class="overflow-hidden rounded-lg w-16 h-8 flex items-center justify-center">
                            ${meta.logo ? `<img src="${meta.logo}" alt="${meta.name}" class="w-full h-full object-cover rounded-lg" onerror="this.style.display='none';">` : `<span class="text-gray-800 font-bold text-xs">${meta.name}</span>`}
                        </div>
                        ${stockStatus}
                    </div>
                    <div class="text-right">
                        <div class="${priceColor}" style="color: ${isCheapest ? '#22c55e' : 'var(--text-primary)'}">${price}</div>
                        <div class="text-xs" style="color: var(--text-tertiary)">${eta}</div>
                    </div>
                </a>
            `;
        }).join("");

        return `
            <div class="rounded-2xl border p-4 flex flex-col gap-4 hover:opacity-90 transition-opacity"
                 style="background-color: var(--bg-elevated); border-color: var(--border-primary)">
                <div class="flex justify-center items-center rounded-lg p-4" style="background-color: var(--bg-secondary)">
                    ${img}
                </div>
                <div>
                    <h3 class="text-base font-semibold leading-snug mb-1" style="color: var(--text-primary)">${name}</h3>
                    <p class="text-sm" style="color: var(--text-secondary)">${quantity}</p>
                </div>
                <div class="space-y-2 flex-1">${platformRows}</div>
            </div>
        `;
    }).join('');
}

// Platform filtering
let lastResults = [];
let activePlatform = 'all';

function filterPlatform(platform) {
    activePlatform = platform;

    document.querySelectorAll("#platform-filters button").forEach(btn => {
        if (btn.dataset.platform === 'all') {
            btn.classList.remove("bg-blue-600", "text-white");
            btn.classList.add("border");
            btn.style.borderColor = "var(--border-primary)";
            btn.style.color = "var(--text-primary)";
        } else {
            btn.classList.remove("border-blue-500");
            btn.classList.add("border");
            btn.style.borderColor = "var(--border-primary)";
        }
    });

    const activeBtn = document.querySelector(`#platform-filters button[data-platform="${platform}"]`);
    if (activeBtn) {
        if (platform === 'all') {
            activeBtn.classList.remove("border");
            activeBtn.classList.add("bg-blue-600", "text-white");
            activeBtn.style.borderColor = "";
            activeBtn.style.color = "";
        } else {
            activeBtn.classList.remove("border");
            activeBtn.style.borderColor = "#3b82f6";
            activeBtn.style.color = "#3b82f6";
        }
    }

    if (platform === "all") {
        renderResults(lastResults);
    } else {
        const filteredResults = lastResults.filter(product => {
            return (product.platforms || []).some(p => {
                const platformName = (p.platform || "").toLowerCase();
                return platformName === platform;
            });
        });
        renderResults(filteredResults);
    }
}

// Loading animation
function startLoadingAnimation() {
    const logos = [
        { src: 'static/assets/zepto_logo.webp', alt: 'Zepto' },
        { src: 'static/assets/Blinkit_logo.webp', alt: 'Blinkit' },
        { src: 'static/assets/Dmart_logo.webp', alt: 'DMart' }
    ];
    let index = 0;

    const interval = setInterval(() => {
        const logoImg = document.getElementById('loading-logo-img');
        if (logoImg) {
            logoImg.src = logos[index].src;
            logoImg.alt = logos[index].alt;
            index = (index + 1) % logos.length;
        }
    }, 1200);

    setTimeout(() => clearInterval(interval), 15000);
    return interval;
}

// Theme toggle functionality
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark');

    if (isDark) {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    } else {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }

    updateThemeIcon(!isDark);
}

function updateThemeIcon(isDark) {
    const themeButton = document.getElementById('theme-toggle');
    const icon = isDark
        ? `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>
           </svg>`
        : `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1M12 20v1M4.2 4.2l.7.7M18.1 18.1l.7.7M1 12h1M22 12h1M4.2 19.8l.7-.7M18.1 5.9l.7-.7M12 7a5 5 0 100 10 5 5 0 000-10z"></path>
           </svg>`;
    themeButton.innerHTML = icon;
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

    if (shouldBeDark) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }

    updateThemeIcon(shouldBeDark);
}

// Google Maps API loading
async function loadGoogleMapsAPI() {
    try {
        const response = await fetch('/config');
        const config = await response.json();

        if (config.maps_api_key) {
            const script = document.getElementById('google-maps-script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${config.maps_api_key}&libraries=places&callback=initializeLocation`;
        } else {
            console.warn('Google Maps API key not found');
            setTimeout(() => {
                if (!loadLocationFromCache()) {
                    detectCurrentLocation();
                } else {
                    updateLocationDisplay();
                }
            }, 1000);
        }
    } catch (error) {
        console.error('Failed to load Google Maps API:', error);
        setTimeout(() => {
            if (!loadLocationFromCache()) {
                detectCurrentLocation();
            } else {
                updateLocationDisplay();
            }
        }, 1000);
    }
}

// Initialize location
function initializeLocation() {
    if (loadLocationFromCache()) {
        updateLocationDisplay();
    } else {
        detectCurrentLocation();
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function () {
    initializeTheme();

    // Main search click
    elements.mainSearch.addEventListener('click', openSearchModal);

    // Location click
    elements.userLocation.addEventListener('click', openLocationModal);

    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

    // Modal close buttons
    document.getElementById('location-back').addEventListener('click', closeLocationModal);
    document.getElementById('location-close').addEventListener('click', closeLocationModal);
    document.getElementById('search-back').addEventListener('click', closeSearchModal);
    document.getElementById('search-close').addEventListener('click', closeSearchModal);

    // Use current location
    document.getElementById('use-current-location').addEventListener('click', () => {
        closeLocationModal();
        detectCurrentLocation();
    });

    // Clear location cache
    document.getElementById('clear-location-cache').addEventListener('click', () => {
        clearLocationCache();
        locationData.address = 'Detecting location...';
        locationData.latitude = null;
        locationData.longitude = null;
        locationData.pincode = null;
        elements.userLocation.textContent = locationData.address;
        closeLocationModal();
        detectCurrentLocation();
    });

    // Search input
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = e.target.value.trim();
            if (query) {
                closeSearchModal();
                performSearch(query);
            }
        }
    });

    // Search input for suggestions with debouncing
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            populateSearchSuggestions(e.target.value);
        }, 150);
    });

    // Location search input handling
    document.getElementById('location-search').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const address = e.target.value.trim();
            if (address) {
                // If Places API didn't handle it, do manual geocoding
                if (window.google && google.maps) {
                    const geocoder = new google.maps.Geocoder();
                    geocoder.geocode({ address: address }, (results, status) => {
                        if (status === 'OK' && results[0]) {
                            updateLocationFromPlace(results[0]);
                            closeLocationModal();
                        } else {
                            // Fallback to manual entry
                            locationData.address = address;
                            updateLocationDisplay();
                            closeLocationModal();
                        }
                    });
                } else {
                    // No Google Maps, just use the entered address
                    locationData.address = address;
                    updateLocationDisplay();
                    closeLocationModal();
                }
            }
        }
    });

    // Back to home
    document.getElementById('back-to-home').addEventListener('click', () => showPage('home'));

    // Clear recent searches
    document.getElementById('clear-recent').addEventListener('click', () => {
        localStorage.removeItem('recent_searches');
        renderRecentSearches();
    });

    // Trending items
    document.querySelectorAll('.trending-item').forEach(item => {
        item.addEventListener('click', () => {
            const product = item.dataset.product;
            performSearch(product);
        });
    });

    // Platform filter buttons
    document.querySelectorAll('#platform-filters button').forEach(button => {
        button.addEventListener('click', () => {
            const platform = button.dataset.platform;
            filterPlatform(platform);
        });
    });

    // Delegate event listeners for dynamic content
    document.addEventListener('click', (e) => {
        // Recent search clicks
        if (e.target.closest('.recent-chip') && !e.target.classList.contains('remove-recent')) {
            const query = e.target.closest('.recent-chip').dataset.query;
            performSearch(query);
        }

        // Remove recent search
        if (e.target.classList.contains('remove-recent')) {
            e.stopPropagation();
            const query = e.target.dataset.query;
            let recent = JSON.parse(localStorage.getItem('recent_searches') || '[]');
            recent = recent.filter(item => item !== query);
            localStorage.setItem('recent_searches', JSON.stringify(recent));
            renderRecentSearches();
        }

        // Search suggestions
        if (e.target.closest('.search-suggestion')) {
            const query = e.target.closest('.search-suggestion').dataset.query;
            closeSearchModal();
            performSearch(query);
        }

        // Location suggestions
        if (e.target.closest('.location-suggestion')) {
            const suggestionElement = e.target.closest('.location-suggestion');
            const placeId = suggestionElement.dataset.placeId;
            if (placeId) {
                selectLocationFromPlaceId(placeId);
            }
        }
    });

    // Initialize
    renderRecentSearches();
    showPage('home');
    loadGoogleMapsAPI();
});

// Google Maps callback
window.initializeLocation = initializeLocation;