package com.example.app.repository;

import com.example.app.domain.entity.Product;
import com.example.app.domain.entity.ProductStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ProductRepository extends
        JpaRepository<Product, UUID>,
        JpaSpecificationExecutor<Product> {

    // Query methods
    Optional<Product> findBySku(String sku);

    boolean existsBySku(String sku);

    Page<Product> findByNameContainingIgnoreCase(String name, Pageable pageable);

    List<Product> findByStatus(ProductStatus status);

    List<Product> findByCategoryId(UUID categoryId);

    Page<Product> findByStatusAndPriceBetween(
        ProductStatus status,
        BigDecimal minPrice,
        BigDecimal maxPrice,
        Pageable pageable
    );

    // JPQL queries
    @Query("""
        SELECT p FROM Product p
        WHERE p.status = :status
        AND p.stockQuantity > 0
        ORDER BY p.createdAt DESC
        """)
    List<Product> findAvailableByStatus(@Param("status") ProductStatus status);

    @Query("""
        SELECT p FROM Product p
        LEFT JOIN FETCH p.category
        WHERE p.id = :id
        """)
    Optional<Product> findByIdWithCategory(@Param("id") UUID id);

    @Query("""
        SELECT p FROM Product p
        WHERE p.featured = true
        AND p.status = 'ACTIVE'
        ORDER BY p.createdAt DESC
        """)
    List<Product> findFeaturedProducts();

    // Native query for complex operations
    @Query(value = """
        SELECT p.* FROM products p
        WHERE p.deleted = false
        AND (
            p.name ILIKE '%' || :search || '%'
            OR p.description ILIKE '%' || :search || '%'
            OR p.sku ILIKE '%' || :search || '%'
        )
        ORDER BY
            CASE WHEN p.name ILIKE :search THEN 1
                 WHEN p.name ILIKE :search || '%' THEN 2
                 ELSE 3
            END,
            p.created_at DESC
        """, nativeQuery = true)
    Page<Product> searchProducts(@Param("search") String search, Pageable pageable);

    // Modifying queries
    @Modifying
    @Query("UPDATE Product p SET p.status = :status WHERE p.id = :id")
    int updateStatus(@Param("id") UUID id, @Param("status") ProductStatus status);

    @Modifying
    @Query("UPDATE Product p SET p.stockQuantity = p.stockQuantity - :quantity WHERE p.id = :id AND p.stockQuantity >= :quantity")
    int decrementStock(@Param("id") UUID id, @Param("quantity") int quantity);

    @Modifying
    @Query("UPDATE Product p SET p.deleted = true, p.deletedAt = :deletedAt WHERE p.id IN :ids")
    int softDeleteByIds(@Param("ids") List<UUID> ids, @Param("deletedAt") Instant deletedAt);

    // Statistics
    @Query("SELECT COUNT(p) FROM Product p WHERE p.status = :status")
    long countByStatus(@Param("status") ProductStatus status);

    @Query("SELECT AVG(p.price) FROM Product p WHERE p.categoryId = :categoryId AND p.status = 'ACTIVE'")
    BigDecimal getAveragePriceByCategory(@Param("categoryId") UUID categoryId);
}
