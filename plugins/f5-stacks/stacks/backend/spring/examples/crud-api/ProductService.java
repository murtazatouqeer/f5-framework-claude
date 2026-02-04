package com.example.app.service;

import com.example.app.domain.entity.Product;
import com.example.app.domain.entity.ProductStatus;
import com.example.app.exception.BusinessException;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.mapper.ProductMapper;
import com.example.app.repository.ProductRepository;
import com.example.app.repository.specification.ProductSpecification;
import com.example.app.web.dto.ProductFilter;
import com.example.app.web.dto.ProductPatchRequest;
import com.example.app.web.dto.ProductRequest;
import com.example.app.web.dto.ProductResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ProductService {

    private final ProductRepository productRepository;
    private final ProductMapper productMapper;
    private final CategoryService categoryService;

    /**
     * Find all products with optional filtering and pagination.
     */
    public Page<ProductResponse> findAll(ProductFilter filter, Pageable pageable) {
        log.debug("Finding products with filter: {}", filter);

        Specification<Product> spec = ProductSpecification.fromFilter(filter);
        Page<Product> page = productRepository.findAll(spec, pageable);

        return page.map(productMapper::toResponse);
    }

    /**
     * Find product by ID.
     */
    @Cacheable(value = "products", key = "#id")
    public ProductResponse findById(UUID id) {
        log.debug("Finding product by id: {}", id);

        return productRepository.findById(id)
            .map(productMapper::toResponse)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));
    }

    /**
     * Find product by SKU.
     */
    public ProductResponse findBySku(String sku) {
        log.debug("Finding product by SKU: {}", sku);

        return productRepository.findBySku(sku)
            .map(productMapper::toResponse)
            .orElseThrow(() -> new ResourceNotFoundException("Product", "sku", sku));
    }

    /**
     * Create new product.
     */
    @Transactional
    public ProductResponse create(ProductRequest request) {
        log.info("Creating product: {}", request.name());

        validateCreate(request);

        Product product = productMapper.toEntity(request);

        // Set category if provided
        if (request.categoryId() != null) {
            product.setCategory(categoryService.findEntityById(request.categoryId()));
        }

        Product saved = productRepository.save(product);

        log.info("Created product with id: {}", saved.getId());
        return productMapper.toResponse(saved);
    }

    /**
     * Update existing product.
     */
    @Transactional
    @CacheEvict(value = "products", key = "#id")
    public ProductResponse update(UUID id, ProductRequest request) {
        log.info("Updating product {}: {}", id, request.name());

        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));

        validateUpdate(product, request);

        productMapper.updateEntity(product, request);

        // Update category if changed
        if (request.categoryId() != null) {
            product.setCategory(categoryService.findEntityById(request.categoryId()));
        } else {
            product.setCategory(null);
        }

        Product updated = productRepository.save(product);

        log.info("Updated product: {}", id);
        return productMapper.toResponse(updated);
    }

    /**
     * Partially update product.
     */
    @Transactional
    @CacheEvict(value = "products", key = "#id")
    public ProductResponse partialUpdate(UUID id, ProductPatchRequest request) {
        log.info("Partial update product {}", id);

        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));

        productMapper.patchEntity(product, request);
        Product updated = productRepository.save(product);

        return productMapper.toResponse(updated);
    }

    /**
     * Delete product (soft delete).
     */
    @Transactional
    @CacheEvict(value = "products", key = "#id")
    public void delete(UUID id) {
        log.info("Deleting product: {}", id);

        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));

        validateDelete(product);

        productRepository.delete(product); // Triggers soft delete via @SQLDelete

        log.info("Deleted product: {}", id);
    }

    /**
     * Update product status.
     */
    @Transactional
    @CacheEvict(value = "products", key = "#id")
    public ProductResponse updateStatus(UUID id, ProductStatus status) {
        log.info("Updating product {} status to {}", id, status);

        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));

        validateStatusTransition(product.getStatus(), status);

        product.setStatus(status);
        Product updated = productRepository.save(product);

        return productMapper.toResponse(updated);
    }

    /**
     * Get featured products.
     */
    @Cacheable(value = "featuredProducts")
    public List<ProductResponse> getFeaturedProducts() {
        return productRepository.findFeaturedProducts().stream()
            .map(productMapper::toResponse)
            .toList();
    }

    // ==================== Validation Methods ====================

    private void validateCreate(ProductRequest request) {
        if (request.sku() != null && productRepository.existsBySku(request.sku())) {
            throw new BusinessException("DUPLICATE_SKU", "Product with SKU already exists: " + request.sku());
        }
    }

    private void validateUpdate(Product existing, ProductRequest request) {
        if (!existing.getStatus().isEditable()) {
            throw new BusinessException("NOT_EDITABLE", "Product in status " + existing.getStatus() + " cannot be edited");
        }

        if (request.sku() != null && !request.sku().equals(existing.getSku())) {
            if (productRepository.existsBySku(request.sku())) {
                throw new BusinessException("DUPLICATE_SKU", "Product with SKU already exists: " + request.sku());
            }
        }
    }

    private void validateDelete(Product product) {
        if (product.getStatus() == ProductStatus.ACTIVE) {
            throw new BusinessException("CANNOT_DELETE_ACTIVE", "Cannot delete active product. Deactivate first.");
        }
    }

    private void validateStatusTransition(ProductStatus current, ProductStatus target) {
        // Define valid transitions
        boolean isValid = switch (current) {
            case DRAFT -> target == ProductStatus.ACTIVE;
            case ACTIVE -> target == ProductStatus.INACTIVE || target == ProductStatus.ARCHIVED;
            case INACTIVE -> target == ProductStatus.ACTIVE || target == ProductStatus.ARCHIVED;
            case ARCHIVED -> false; // Cannot transition from ARCHIVED
        };

        if (!isValid) {
            throw new BusinessException("INVALID_STATUS_TRANSITION",
                "Cannot transition from " + current + " to " + target);
        }
    }
}
