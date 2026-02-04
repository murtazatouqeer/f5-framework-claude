package com.example.app.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

@Entity
@Table(name = "roles")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Role {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "name", nullable = false, unique = true, length = 50)
    private String name;

    @Column(name = "description", length = 255)
    private String description;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "role_permissions", joinColumns = @JoinColumn(name = "role_id"))
    @Column(name = "permission")
    @Builder.Default
    private Set<String> permissions = new HashSet<>();

    // Standard roles
    public static final String ADMIN = "ADMIN";
    public static final String MANAGER = "MANAGER";
    public static final String USER = "USER";

    // Permissions
    public static final String PERM_USER_READ = "user:read";
    public static final String PERM_USER_WRITE = "user:write";
    public static final String PERM_USER_DELETE = "user:delete";
    public static final String PERM_PRODUCT_READ = "product:read";
    public static final String PERM_PRODUCT_WRITE = "product:write";
    public static final String PERM_PRODUCT_DELETE = "product:delete";
    public static final String PERM_ORDER_READ = "order:read";
    public static final String PERM_ORDER_WRITE = "order:write";

    public void addPermission(String permission) {
        permissions.add(permission);
    }

    public void removePermission(String permission) {
        permissions.remove(permission);
    }

    public boolean hasPermission(String permission) {
        return permissions.contains(permission);
    }
}
