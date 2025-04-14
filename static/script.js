// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  
  // Set copyright year
  document.getElementById('copyright-year').textContent = new Date().getFullYear();
  
  // Initialize components
  initMobileMenu();
  initSearchBar();
  initCategoryFilter();
  initBookCards();
  initReadingList();
});

// Mobile menu toggle
function initMobileMenu() {
  const toggleButton = document.getElementById('mobile-menu-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  const menuIcon = toggleButton.querySelector('[data-lucide="menu"]');
  
  toggleButton.addEventListener('click', () => {
    if (mobileMenu.classList.contains('open')) {
      mobileMenu.classList.remove('open');
      menuIcon.setAttribute('name', 'menu');
      lucide.createIcons();
    } else {
      mobileMenu.classList.add('open');
      menuIcon.setAttribute('name', 'x');
      lucide.createIcons();
    }
  });
}

// Search bar functionality
function initSearchBar() {
  const searchForm = document.getElementById('search-form');
  const searchInput = document.getElementById('search-input');
  const clearButton = document.getElementById('clear-search');
  
  // Show/hide clear button based on input
  searchInput.addEventListener('input', () => {
    if (searchInput.value) {
      clearButton.style.display = 'flex';
    } else {
      clearButton.style.display = 'none';
    }
  });
  
  // Clear search input
  clearButton.addEventListener('click', () => {
    searchInput.value = '';
    clearButton.style.display = 'none';
    searchInput.focus();
  });
  
  // Handle search form submission
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    console.log('Searching for:', searchInput.value);
    // Here you would typically trigger a search function
  });
}

// Category filter functionality
function initCategoryFilter() {
  // Mock categories data
  const categories = [
    "All Genres",
    "Fiction",
    "Science Fiction",
    "Fantasy",
    "Mystery",
    "Thriller",
    "Romance",
    "Biography",
    "History",
    "Self-Help",
    "Business"
  ];
  
  let selectedCategory = "All Genres";
  const bookListTitle = document.getElementById('book-list-title');
  
  // Mobile dropdown implementation
  const dropdownBtn = document.getElementById('category-dropdown-btn');
  const dropdownMenu = document.getElementById('category-dropdown-menu');
  
  // Populate dropdown menu
  categories.forEach(category => {
    const item = document.createElement('button');
    item.className = 'dropdown-item';
    if (category === selectedCategory) {
      item.classList.add('selected');
    }
    
    item.textContent = category;
    
    if (category === selectedCategory) {
      const checkIcon = document.createElement('span');
      checkIcon.innerHTML = '<i data-lucide="check" class="dropdown-check"></i>';
      item.appendChild(checkIcon);
    }
    
    item.addEventListener('click', () => {
      selectCategory(category);
      dropdownMenu.style.display = 'none';
      dropdownBtn.classList.remove('open');
    });
    
    dropdownMenu.appendChild(item);
  });
  
  // Toggle dropdown
  dropdownBtn.addEventListener('click', () => {
    if (dropdownMenu.style.display === 'block') {
      dropdownMenu.style.display = 'none';
      dropdownBtn.classList.remove('open');
    } else {
      dropdownMenu.style.display = 'block';
      dropdownBtn.classList.add('open');
      lucide.createIcons();
    }
  });
  
  // Close dropdown when clicking elsewhere
  document.addEventListener('click', (e) => {
    if (!dropdownBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
      dropdownMenu.style.display = 'none';
      dropdownBtn.classList.remove('open');
    }
  });
  
  // Desktop category pills
  const categoryPillsContainer = document.querySelector('.category-pills');
  
  categories.forEach(category => {
    const pill = document.createElement('button');
    pill.className = 'category-pill';
    if (category === selectedCategory) {
      pill.classList.add('active');
    }
    
    pill.textContent = category;
    
    pill.addEventListener('click', () => {
      selectCategory(category);
    });
    
    categoryPillsContainer.appendChild(pill);
  });
  
  // Function to handle category selection
  function selectCategory(category) {
    selectedCategory = category;
    
    // Update UI
    document.getElementById('selected-category').textContent = category;
    
    // Update book list title
    if (category === "All Genres") {
      bookListTitle.textContent = "Recommended For You";
    } else {
      bookListTitle.textContent = `${category} Books`;
    }
    
    // Update dropdown
    const dropdownItems = document.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => {
      if (item.textContent === category) {
        item.classList.add('selected');
        
        // Add check icon if it doesn't exist
        if (!item.querySelector('.dropdown-check')) {
          const checkIcon = document.createElement('span');
          checkIcon.innerHTML = '<i data-lucide="check" class="dropdown-check"></i>';
          item.appendChild(checkIcon);
        }
      } else {
        item.classList.remove('selected');
        const checkIcon = item.querySelector('.dropdown-check');
        if (checkIcon) {
          item.removeChild(checkIcon.parentNode);
        }
      }
    });
    
    // Update pills
    const pills = document.querySelectorAll('.category-pill');
    pills.forEach(pill => {
      if (pill.textContent === category) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });
    
    // Filter books
    filterBooks(category);
    
    // Update icons
    lucide.createIcons();
  }
}

// Book cards functionality
function initBookCards() {
  // Mock books data
  const mockBooks = [
    {
      id: "1",
      title: "The Midnight Library",
      author: "Matt Haig",
      coverImage: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=387&q=80",
      rating: 4.2,
      categories: ["Fiction", "Fantasy", "Self-Help"]
    },
    {
      id: "2",
      title: "Atomic Habits",
      author: "James Clear",
      coverImage: "https://images.unsplash.com/photo-1589998059171-988d887df646?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1176&q=80",
      rating: 4.8,
      categories: ["Self-Help", "Psychology", "Productivity"]
    },
    {
      id: "3",
      title: "Project Hail Mary",
      author: "Andy Weir",
      coverImage: "https://images.unsplash.com/photo-1465929639680-64ee080eb3ed?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1170&q=80",
      rating: 4.6,
      categories: ["Science Fiction", "Adventure"]
    },
    {
      id: "4",
      title: "Where the Crawdads Sing",
      author: "Delia Owens",
      coverImage: "https://images.unsplash.com/photo-1531901599143-df5012228b10?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1931&q=80",
      rating: 4.5,
      categories: ["Fiction", "Mystery", "Coming of Age"]
    },
    {
      id: "5",
      title: "The Psychology of Money",
      author: "Morgan Housel",
      coverImage: "https://images.unsplash.com/photo-1535320903710-d993d3d77d29?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1170&q=80",
      rating: 4.7,
      categories: ["Finance", "Psychology", "Self-Help"]
    },
    {
      id: "6",
      title: "The Silent Patient",
      author: "Alex Michaelides",
      coverImage: "https://images.unsplash.com/photo-1476275466078-4007374efbbe?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1129&q=80",
      rating: 4.3,
      categories: ["Thriller", "Mystery", "Psychological"]
    }
  ];
  
  // Create book cards
  renderBookCards(mockBooks, document.getElementById('books-container'));
  
  // New releases books
  const newReleases = [
    {
      id: "7",
      title: "Tomorrow, and Tomorrow, and Tomorrow",
      author: "Gabrielle Zevin",
      coverImage: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=387&q=80",
      rating: 4.5,
      categories: ["Fiction", "Contemporary"]
    },
    {
      id: "8",
      title: "Lessons in Chemistry",
      author: "Bonnie Garmus",
      coverImage: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=387&q=80",
      rating: 4.7,
      categories: ["Fiction", "Historical"]
    }
  ];
  
  renderBookCards(newReleases, document.querySelector('.new-releases-grid'));
  
  // Mystery & Thriller books
  const mysteryThrillerBooks = [
    {
      id: "9",
      title: "The Last Thing He Told Me",
      author: "Laura Dave",
      coverImage: "https://images.unsplash.com/photo-1476275466078-4007374efbbe?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1129&q=80",
      rating: 4.1,
      categories: ["Mystery", "Thriller"]
    },
    {
      id: "10",
      title: "Verity",
      author: "Colleen Hoover",
      coverImage: "https://images.unsplash.com/photo-1476275466078-4007374efbbe?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1129&q=80",
      rating: 4.4,
      categories: ["Thriller", "Romance"]
    },
    {
      id: "11",
      title: "The Guest List",
      author: "Lucy Foley",
      coverImage: "https://images.unsplash.com/photo-1476275466078-4007374efbbe?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1129&q=80",
      rating: 4.2,
      categories: ["Mystery", "Thriller"]
    },
    {
      id: "12",
      title: "The Paris Apartment",
      author: "Lucy Foley",
      coverImage: "https://images.unsplash.com/photo-1476275466078-4007374efbbe?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1129&q=80",
      rating: 3.9,
      categories: ["Mystery", "Thriller"]
    }
  ];
  
  renderBookCards(mysteryThrillerBooks, document.getElementById('mystery-thriller-books'));
}

// Reading list functionality
function initReadingList() {
  // Mock reading list data
  const mockReadingList = [
    {
      id: "1",
      title: "The Midnight Library",
      author: "Matt Haig",
      coverImage: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=387&q=80",
      status: "reading", // reading, completed, to-read
      progress: 45 // percentage
    },
    {
      id: "3",
      title: "Project Hail Mary",
      author: "Andy Weir",
      coverImage: "https://images.unsplash.com/photo-1465929639680-64ee080eb3ed?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1170&q=80",
      status: "to-read",
      progress: 0
    },
    {
      id: "6",
      title: "The Silent Patient",
      author: "Alex Michaelides",
      coverImage: "https://images.unsplash.com/photo-1476275466078-4007374efbbe?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1129&q=80",
      status: "completed",
      progress: 100
    }
  ];
  
  renderReadingList(mockReadingList);
  
  // Tab functionality
  const tabButtons = document.querySelectorAll('.tab-btn');
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const filter = button.getAttribute('data-filter');
      
      // Update active tab
      tabButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      
      // Filter the reading list
      filterReadingList(filter);
    });
  });
}

// Helper functions
function renderBookCards(books, container) {
  container.innerHTML = '';
  
  books.forEach(book => {
    const bookCard = createBookCard(book);
    container.appendChild(bookCard);
  });
  
  // Initialize Lucide icons in the new cards
  lucide.createIcons();
}

function createBookCard(book) {
  const card = document.createElement('div');
  card.className = 'book-card';
  card.setAttribute('data-id', book.id);
  card.setAttribute('data-categories', book.categories.join(','));
  
  // Create saved state (for heart icon toggle)
  let isSaved = false;
  
  card.innerHTML = `
    <div class="book-cover-container">
      <img src="${book.coverImage}" alt="${book.title} cover" class="book-cover">
      <div class="book-overlay">
        <div class="book-overlay-buttons">
          <button class="btn btn-white">
            <i data-lucide="book-open" class="btn-icon"></i>
            Preview
          </button>
          <button class="btn btn-secondary save-button">
            <i data-lucide="heart" class="btn-icon ${isSaved ? 'saved' : ''}"></i>
            ${isSaved ? 'Saved' : 'Save for Later'}
          </button>
        </div>
      </div>
    </div>
    
    <div class="book-details">
      <div class="book-header">
        <h3 class="book-title">${book.title}</h3>
        <div class="book-rating">
          <i data-lucide="star" class="star-icon"></i>
          <span class="rating-value">${book.rating}</span>
        </div>
      </div>
      
      <p class="book-author">${book.author}</p>
      
      <div class="book-categories">
        ${book.categories.slice(0, 2).map(category => 
          `<span class="category-pill">${category}</span>`
        ).join('')}
        ${book.categories.length > 2 ? 
          `<span class="category-pill">+${book.categories.length - 2}</span>` : ''}
      </div>
    </div>
  `;
  
  // Add event listener to save button after card is created
  setTimeout(() => {
    const saveButton = card.querySelector('.save-button');
    if (saveButton) {
      saveButton.addEventListener('click', (e) => {
        e.preventDefault();
        
        isSaved = !isSaved;
        
        const heartIcon = saveButton.querySelector('[data-lucide="heart"]');
        
        if (isSaved) {
          heartIcon.classList.add('saved');
          saveButton.innerHTML = `
            <i data-lucide="heart" class="btn-icon saved"></i>
            Saved
          `;
        } else {
          heartIcon.classList.remove('saved');
          saveButton.innerHTML = `
            <i data-lucide="heart" class="btn-icon"></i>
            Save for Later
          `;
        }
        
        // Update the Lucide icon
        lucide.createIcons();
      });
    }
  }, 0);
  
  return card;
}

function renderReadingList(books) {
  const container = document.getElementById('reading-list-books');
  container.innerHTML = '';
  
  if (books.length === 0) {
    container.innerHTML = `
      <div class="reading-list-empty">
        <p>No books in this list yet.</p>
      </div>
    `;
    return;
  }
  
  books.forEach(book => {
    const bookElement = document.createElement('div');
    bookElement.className = 'reading-list-book';
    bookElement.setAttribute('data-status', book.status);
    
    let statusHTML = '';
    
    if (book.status === 'reading') {
      statusHTML = `
        <div class="reading-progress">
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${book.progress}%"></div>
          </div>
          <p class="progress-text">${book.progress}% complete</p>
        </div>
      `;
    } else if (book.status === 'completed') {
      statusHTML = `
        <div class="reading-status completed">
          <i data-lucide="check" class="reading-status-icon"></i>
          Completed
        </div>
      `;
    } else {
      statusHTML = `
        <div class="reading-status to-read">
          <i data-lucide="clock" class="reading-status-icon"></i>
          Not started
        </div>
      `;
    }
    
    bookElement.innerHTML = `
      <img src="${book.coverImage}" alt="${book.title} cover" class="reading-list-book-cover">
      
      <div class="reading-list-book-info">
        <h3 class="reading-list-book-title">${book.title}</h3>
        <p class="reading-list-book-author">${book.author}</p>
        ${statusHTML}
      </div>
      
      <button class="reading-list-remove" data-id="${book.id}">
        <i data-lucide="x" class="reading-list-remove-icon"></i>
      </button>
    `;
    
    container.appendChild(bookElement);
  });
  
  // Add event listeners for remove buttons
  const removeButtons = document.querySelectorAll('.reading-list-remove');
  removeButtons.forEach(button => {
    button.addEventListener('click', () => {
      const id = button.getAttribute('data-id');
      const bookElement = button.closest('.reading-list-book');
      
      // Remove with animation
      bookElement.style.opacity = '0';
      setTimeout(() => {
        bookElement.remove();
        
        // Check if reading list is empty
        if (document.querySelectorAll('.reading-list-book').length === 0) {
          container.innerHTML = `
            <div class="reading-list-empty">
              <p>No books in this list yet.</p>
            </div>
          `;
        }
      }, 300);
    });
  });
  
  // Initialize Lucide icons in the reading list
  lucide.createIcons();
}

function filterReadingList(filter) {
  const books = document.querySelectorAll('.reading-list-book');
  
  books.forEach(book => {
    if (filter === 'all' || book.getAttribute('data-status') === filter) {
      book.style.display = 'flex';
    } else {
      book.style.display = 'none';
    }
  });
  
  // Check if no books are visible
  let visibleCount = 0;
  books.forEach(book => {
    if (book.style.display !== 'none') {
      visibleCount++;
    }
  });
  
  const container = document.getElementById('reading-list-books');
  
  if (visibleCount === 0) {
    if (!document.querySelector('.reading-list-empty')) {
      const emptyMessage = document.createElement('div');
      emptyMessage.className = 'reading-list-empty';
      emptyMessage.innerHTML = `<p>No books in this list yet.</p>`;
      container.appendChild(emptyMessage);
    }
  } else {
    const emptyMessage = document.querySelector('.reading-list-empty');
    if (emptyMessage) {
      emptyMessage.remove();
    }
  }
}

function filterBooks(category) {
  const mainBooksContainer = document.getElementById('books-container');
  const allBooks = document.querySelectorAll('[data-categories]');
  
  // Only filter the main book container, not other sections
  const booksToFilter = Array.from(mainBooksContainer.querySelectorAll('[data-categories]'));
  
  if (category === "All Genres") {
    booksToFilter.forEach(book => {
      book.style.display = 'block';
    });
  } else {
    booksToFilter.forEach(book => {
      const bookCategories = book.getAttribute('data-categories').split(',');
      
      if (bookCategories.includes(category)) {
        book.style.display = 'block';
      } else {
        book.style.display = 'none';
      }
    });
  }
  
  // Check if no books are visible
  let visibleCount = 0;
  booksToFilter.forEach(book => {
    if (book.style.display !== 'none') {
      visibleCount++;
    }
  });
  
  if (visibleCount === 0) {
    if (!mainBooksContainer.querySelector('.no-books-message')) {
      const message = document.createElement('div');
      message.className = 'text-center py-10 no-books-message';
      message.innerHTML = `
        <p class="text-lg text-muted-foreground">No books found in this category.</p>
        <p class="mt-2">Try selecting a different category.</p>
      `;
      mainBooksContainer.appendChild(message);
    }
  } else {
    const message = mainBooksContainer.querySelector('.no-books-message');
    if (message) {
      message.remove();
    }
  }
}