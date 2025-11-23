let swiperInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    // Fetch dates first to populate sidebar
    fetchDates();
    
    // Load all images by default
    loadImages();
});

function fetchDates() {
    fetch('/api/dates')
        .then(response => response.json())
        .then(dates => {
            const nav = document.getElementById('date-nav');
            
            // Add "All Images" link
            const allLink = document.createElement('a');
            allLink.href = "#";
            allLink.textContent = "Toutes les dates";
            allLink.className = "active";
            allLink.onclick = (e) => {
                e.preventDefault();
                setActiveLink(allLink);
                loadImages();
            };
            nav.appendChild(allLink);
            
            dates.forEach(date => {
                const link = document.createElement('a');
                link.href = "#";
                link.textContent = date;
                link.onclick = (e) => {
                    e.preventDefault();
                    setActiveLink(link);
                    loadImages(date);
                };
                nav.appendChild(link);
            });
        })
        .catch(error => console.error('Error loading dates:', error));
}

function setActiveLink(element) {
    document.querySelectorAll('#date-nav a').forEach(a => a.classList.remove('active'));
    element.classList.add('active');
}

function loadImages(date = null) {
    let url = '/api/images';
    if (date) {
        url += `?date=${encodeURIComponent(date)}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            initSlideshow(data);
        })
        .catch(error => console.error('Error loading images:', error));
}

function initSlideshow(images) {
    const wrapper = document.getElementById('swiper-wrapper');
    wrapper.innerHTML = ''; // Clear existing slides
    
    if (images.length === 0) {
        wrapper.innerHTML = '<div class="swiper-slide">No images found</div>';
        updateInfo(null);
        return;
    }

    // Create slides
    images.forEach(img => {
        const slide = document.createElement('div');
        slide.className = 'swiper-slide';
        
        const imageElement = document.createElement('img');
        imageElement.src = `/images/${img.label}`;
        imageElement.alt = img.label;
        imageElement.loading = "lazy";
        
        slide.appendChild(imageElement);
        wrapper.appendChild(slide);
    });

    // Destroy existing swiper if present
    if (swiperInstance) {
        swiperInstance.destroy(true, true);
    }

    // Initialize Swiper
    swiperInstance = new Swiper(".mySwiper", {
        navigation: {
            nextEl: ".swiper-button-next",
            prevEl: ".swiper-button-prev",
        },
        pagination: {
            el: ".swiper-pagination",
            clickable: true,
        },
        keyboard: {
            enabled: true,
        },
        observer: true,
        observeParents: true,
        on: {
            init: function () {
                if (images.length > 0) {
                    updateInfo(images[this.activeIndex]);
                }
            },
            slideChange: function () {
                if (images.length > 0) {
                    updateInfo(images[this.activeIndex]);
                }
            },
        },
    });
    
    // Force update for first slide
    if (images.length > 0) {
        updateInfo(images[0]);
    }
}

function updateInfo(data) {
    if (!data) {
        document.getElementById('img-label').textContent = '-';
        document.getElementById('img-date').textContent = '-';
        document.getElementById('img-time').textContent = '-';
        document.getElementById('img-location').textContent = '-';
        document.getElementById('img-dims').textContent = '-';
        document.getElementById('img-size').textContent = '-';
        document.getElementById('img-res').textContent = '-';
        return;
    }
    
    document.getElementById('img-label').textContent = data.label || '-';
    document.getElementById('img-date').textContent = data.date || '-';
    document.getElementById('img-time').textContent = data.heure || '-';
    document.getElementById('img-location').textContent = data.lieu || '-';
    document.getElementById('img-dims').textContent = `${data.largeur} x ${data.hauteur}`;
    document.getElementById('img-size').textContent = data.taille || '-';
    document.getElementById('img-res').textContent = data['résolution'] || '-';
}
