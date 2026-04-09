let allItems = [];

async function fetchInventory() {
    try {
        const response = await fetch('/api/inventory');
        allItems = await response.json();
        renderTable(allItems);
    } catch (error) {
        console.error('Error fetching inventory:', error);
        document.getElementById('tableBody').innerHTML = '<tr><td colspan="8" class="text-center text-danger">Failed to load data.</td></tr>';
    }
}

function renderTable(items) {
    const tbody = document.getElementById('tableBody');
    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No items found.</td></tr>';
        return;
    }
    let html = '';
    items.forEach(item => {
        html += `<tr>
            <td>${item.id}</td>
            <td>${item.name}</td>
            <td><span class="badge bg-info text-dark">${item.category}</span></td>
            <td>${item.size}</td>
            <td>${item.color}</td>
            <td>₹${item.price.toFixed(2)}</td>
            <td>${item.stock_quantity}</td>
            <td>
                <a href="/inventory/edit/${item.id}" class="btn btn-sm btn-outline-secondary"><i class="fas fa-edit"></i></a>
                <a href="/inventory/delete/${item.id}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete this item?')"><i class="fas fa-trash"></i></a>
            </td>
        </tr>`;
    });
    tbody.innerHTML = html;
}

function filterItems() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const category = document.getElementById('categoryFilter').value;

    const filtered = allItems.filter(item => {
        const matchesSearch = item.name.toLowerCase().includes(searchTerm) ||
                              item.category.toLowerCase().includes(searchTerm) ||
                              item.color.toLowerCase().includes(searchTerm);
        const matchesCategory = category === '' || item.category === category;
        return matchesSearch && matchesCategory;
    });
    renderTable(filtered);
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    fetchInventory();

    document.getElementById('searchInput').addEventListener('input', filterItems);
    document.getElementById('categoryFilter').addEventListener('change', filterItems);
    document.getElementById('refreshBtn').addEventListener('click', () => {
        fetchInventory();
        document.getElementById('searchInput').value = '';
        document.getElementById('categoryFilter').value = '';
    });
});