// Books Manager API Utilities and Enhanced JavaScript

class BooksManager {
    constructor() {
        this.apiBase = window.location.origin + '/api';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeTabs();
    }

    // API Methods
    async fetchBooks() {
        try {
            const response = await fetch(`${this.apiBase}/books/`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching books:', error);
            return [];
        }
    }

    async fetchCategories() {
        try {
            const response = await fetch(`${this.apiBase}/categories/`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching categories:', error);
            return [];
        }
    }

    async searchBooks(query) {
        try {
            const response = await fetch(`${this.apiBase}/books/search/${encodeURIComponent(query)}`);
            return await response.json();
        } catch (error) {
            console.error('Error searching books:', error);
            return [];
        }
    }

    // UI Methods
    setupEventListeners() {
        // Newsletter subscription
        const newsletterForm = document.getElementById('newsletter-form');
        if (newsletterForm) {
            newsletterForm.addEventListener('submit', (e) => this.handleNewsletterSubmit(e));
        }

        // Add to cart functionality
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-to-cart') || e.target.closest('.add-to-cart')) {
                const button = e.target.classList.contains('add-to-cart') ? e.target : e.target.closest('.add-to-cart');
                this.handleAddToCart(button);
            }
        });

        // Search functionality
        const searchForm = document.querySelector('.search-box');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }
    }

    initializeTabs() {
        // Enhanced tab functionality with smooth transitions
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.handleTabClick(e));
        });
    }

    handleNewsletterSubmit(e) {
        e.preventDefault();
        const email = e.target.querySelector('input[name="email"]').value;
        const button = e.target.querySelector('.btn-subscribe');
        const originalText = button.innerHTML;
        
        // Show loading state
        button.innerHTML = '<span>Subscribing...</span>';
        button.disabled = true;

        // Simulate API call (replace with actual endpoint)
        setTimeout(() => {
            this.showSuccessMessage(`Thank you! We'll send updates to ${email}`);
            e.target.reset();
            button.innerHTML = originalText;
            button.disabled = false;
        }, 1000);
    }

    handleAddToCart(button) {
        const bookId = button.getAttribute('data-book-id');
        const originalText = button.textContent;
        
        // Show loading state
        button.textContent = 'Adding...';
        button.disabled = true;
        button.classList.add('loading');

        // Simulate API call to add to cart
        setTimeout(() => {
            button.textContent = 'Added!';
            button.classList.remove('loading');
            button.classList.add('btn-success');
            
            // Reset after delay
            setTimeout(() => {
                button.textContent = originalText;
                button.disabled = false;
                button.classList.remove('btn-success');
            }, 2000);
        }, 500);

        console.log('Adding book to cart:', bookId);
    }

    handleSearch(e) {
        e.preventDefault();
        const query = e.target.querySelector('.search-input').value.trim();
        if (query) {
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
    }

    handleTabClick(e) {
        const target = e.target.getAttribute('data-tab-target');
        
        if (!target) return;

        // Remove active class from all tabs and content
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('[data-tab-content]').forEach(content => {
            content.classList.remove('active');
        });
        
        // Add active class to clicked tab and corresponding content
        e.target.classList.add('active');
        const targetContent = document.querySelector(target);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    }

    showSuccessMessage(message) {
        const alert = document.createElement('div');
        alert.className = 'success-message';
        alert.textContent = message;
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 300px;
        `;
        
        document.body.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, 4000);
    }

    // Utility method to format book data
    formatBookCard(book) {
        const coverUrl = book.cover_id 
            ? `https://covers.openlibrary.org/b/id/${book.cover_id}-M.jpg`
            : '/static/images/default.png';
            
        const authors = book.authors && book.authors.length > 0 
            ? book.authors.join(', ')
            : 'Unknown Author';

        return {
            ...book,
            coverUrl,
            authorsString: authors,
            price: ((book.id * 7.99) % 50 + 15).toFixed(2)
        };
    }
}

// Initialize the Books Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.booksManager = new BooksManager();
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading states for book covers
    document.querySelectorAll('img[src*="covers.openlibrary.org"]').forEach(img => {
        img.addEventListener('load', function() {
            this.style.opacity = '1';
        });
        img.addEventListener('error', function() {
            this.src = '/static/images/default.png';
        });
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.3s ease';
    });
});