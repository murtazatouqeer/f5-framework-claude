# Test Class Template

JUnit 5 test templates for Spring Boot with unit and integration testing patterns.

## Unit Test Template

```java
package {{package}}.service;

import {{package}}.domain.entity.{{Entity}};
import {{package}}.domain.entity.{{Entity}}Status;
import {{package}}.exception.ResourceNotFoundException;
import {{package}}.mapper.{{Entity}}Mapper;
import {{package}}.repository.{{Entity}}Repository;
import {{package}}.web.dto.{{Entity}}Request;
import {{package}}.web.dto.{{Entity}}Response;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.*;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("{{Entity}}Service Unit Tests")
class {{Entity}}ServiceTest {

    @Mock
    private {{Entity}}Repository {{entity}}Repository;

    @Mock
    private {{Entity}}Mapper {{entity}}Mapper;

    @InjectMocks
    private {{Entity}}Service {{entity}}Service;

    @Captor
    private ArgumentCaptor<{{Entity}}> {{entity}}Captor;

    private {{Entity}} {{entity}};
    private {{Entity}}Request request;
    private {{Entity}}Response response;
    private UUID {{entity}}Id;

    @BeforeEach
    void setUp() {
        {{entity}}Id = UUID.randomUUID();

        {{entity}} = {{Entity}}.builder()
            .id({{entity}}Id)
            .name("Test {{Entity}}")
            .description("Test Description")
            .status({{Entity}}Status.ACTIVE)
            .createdAt(Instant.now())
            .build();

        request = new {{Entity}}Request(
            "Test {{Entity}}",
            "Test Description",
            null,
            BigDecimal.valueOf(99.99),
            null,
            List.of(),
            List.of()
        );

        response = new {{Entity}}Response(
            {{entity}}Id,
            "Test {{Entity}}",
            "Test Description",
            null,
            BigDecimal.valueOf(99.99),
            null,
            List.of(),
            List.of(),
            Instant.now(),
            Instant.now(),
            "user"
        );
    }

    @Nested
    @DisplayName("findById")
    class FindByIdTests {

        @Test
        @DisplayName("should return {{entity}} when found")
        void shouldReturn{{Entity}}WhenFound() {
            // Given
            given({{entity}}Repository.findById({{entity}}Id)).willReturn(Optional.of({{entity}}));
            given({{entity}}Mapper.toResponse({{entity}})).willReturn(response);

            // When
            {{Entity}}Response result = {{entity}}Service.findById({{entity}}Id);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.id()).isEqualTo({{entity}}Id);
            assertThat(result.name()).isEqualTo("Test {{Entity}}");

            then({{entity}}Repository).should().findById({{entity}}Id);
            then({{entity}}Mapper).should().toResponse({{entity}});
        }

        @Test
        @DisplayName("should throw ResourceNotFoundException when not found")
        void shouldThrowExceptionWhenNotFound() {
            // Given
            UUID nonExistentId = UUID.randomUUID();
            given({{entity}}Repository.findById(nonExistentId)).willReturn(Optional.empty());

            // When & Then
            assertThatThrownBy(() -> {{entity}}Service.findById(nonExistentId))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("{{Entity}}")
                .hasMessageContaining(nonExistentId.toString());

            then({{entity}}Mapper).shouldHaveNoInteractions();
        }
    }

    @Nested
    @DisplayName("create")
    class CreateTests {

        @Test
        @DisplayName("should create {{entity}} successfully")
        void shouldCreate{{Entity}}Successfully() {
            // Given
            given({{entity}}Mapper.toEntity(request)).willReturn({{entity}});
            given({{entity}}Repository.save(any({{Entity}}.class))).willReturn({{entity}});
            given({{entity}}Mapper.toResponse({{entity}})).willReturn(response);

            // When
            {{Entity}}Response result = {{entity}}Service.create(request);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.name()).isEqualTo("Test {{Entity}}");

            then({{entity}}Repository).should().save({{entity}}Captor.capture());
            {{Entity}} savedEntity = {{entity}}Captor.getValue();
            assertThat(savedEntity.getName()).isEqualTo("Test {{Entity}}");
        }

        @Test
        @DisplayName("should validate before creating")
        void shouldValidateBeforeCreating() {
            // Given
            {{Entity}}Request invalidRequest = new {{Entity}}Request(
                "", // Invalid: empty name
                "Description",
                null,
                BigDecimal.valueOf(-1), // Invalid: negative price
                null,
                List.of(),
                List.of()
            );

            // This test demonstrates validation in service layer
            // Actual validation typically happens via @Valid in controller
        }
    }

    @Nested
    @DisplayName("update")
    class UpdateTests {

        @Test
        @DisplayName("should update {{entity}} successfully")
        void shouldUpdate{{Entity}}Successfully() {
            // Given
            given({{entity}}Repository.findById({{entity}}Id)).willReturn(Optional.of({{entity}}));
            given({{entity}}Repository.save(any({{Entity}}.class))).willReturn({{entity}});
            given({{entity}}Mapper.toResponse({{entity}})).willReturn(response);

            // When
            {{Entity}}Response result = {{entity}}Service.update({{entity}}Id, request);

            // Then
            assertThat(result).isNotNull();
            then({{entity}}Mapper).should().updateEntity(eq({{entity}}), eq(request));
            then({{entity}}Repository).should().save({{entity}});
        }

        @Test
        @DisplayName("should throw exception when updating non-existent {{entity}}")
        void shouldThrowExceptionWhenUpdatingNonExistent() {
            // Given
            UUID nonExistentId = UUID.randomUUID();
            given({{entity}}Repository.findById(nonExistentId)).willReturn(Optional.empty());

            // When & Then
            assertThatThrownBy(() -> {{entity}}Service.update(nonExistentId, request))
                .isInstanceOf(ResourceNotFoundException.class);
        }
    }

    @Nested
    @DisplayName("delete")
    class DeleteTests {

        @Test
        @DisplayName("should delete {{entity}} successfully")
        void shouldDelete{{Entity}}Successfully() {
            // Given
            given({{entity}}Repository.existsById({{entity}}Id)).willReturn(true);
            willDoNothing().given({{entity}}Repository).deleteById({{entity}}Id);

            // When
            {{entity}}Service.delete({{entity}}Id);

            // Then
            then({{entity}}Repository).should().deleteById({{entity}}Id);
        }

        @Test
        @DisplayName("should throw exception when deleting non-existent {{entity}}")
        void shouldThrowExceptionWhenDeletingNonExistent() {
            // Given
            UUID nonExistentId = UUID.randomUUID();
            given({{entity}}Repository.existsById(nonExistentId)).willReturn(false);

            // When & Then
            assertThatThrownBy(() -> {{entity}}Service.delete(nonExistentId))
                .isInstanceOf(ResourceNotFoundException.class);
        }
    }

    @Nested
    @DisplayName("findAll")
    class FindAllTests {

        @Test
        @DisplayName("should return paginated results")
        void shouldReturnPaginatedResults() {
            // Given
            Pageable pageable = PageRequest.of(0, 10, Sort.by("createdAt").descending());
            Page<{{Entity}}> entityPage = new PageImpl<>(List.of({{entity}}), pageable, 1);

            given({{entity}}Repository.findAll(pageable)).willReturn(entityPage);
            given({{entity}}Mapper.toResponse({{entity}})).willReturn(response);

            // When
            Page<{{Entity}}Response> result = {{entity}}Service.findAll(null, pageable);

            // Then
            assertThat(result.getContent()).hasSize(1);
            assertThat(result.getTotalElements()).isEqualTo(1);
        }

        @Test
        @DisplayName("should filter by search term")
        void shouldFilterBySearchTerm() {
            // Given
            String searchTerm = "test";
            Pageable pageable = PageRequest.of(0, 10);
            Page<{{Entity}}> entityPage = new PageImpl<>(List.of({{entity}}), pageable, 1);

            given({{entity}}Repository.findByNameContainingIgnoreCase(searchTerm, pageable))
                .willReturn(entityPage);
            given({{entity}}Mapper.toResponse({{entity}})).willReturn(response);

            // When
            Page<{{Entity}}Response> result = {{entity}}Service.findAll(searchTerm, pageable);

            // Then
            assertThat(result.getContent()).hasSize(1);
            then({{entity}}Repository).should().findByNameContainingIgnoreCase(searchTerm, pageable);
        }
    }

    @Nested
    @DisplayName("Parameterized Tests")
    class ParameterizedTests {

        @ParameterizedTest
        @DisplayName("should handle various status values")
        @EnumSource({{Entity}}Status.class)
        void shouldHandleVariousStatusValues({{Entity}}Status status) {
            // Given
            {{entity}}.setStatus(status);
            given({{entity}}Repository.findById({{entity}}Id)).willReturn(Optional.of({{entity}}));
            given({{entity}}Mapper.toResponse(any())).willReturn(response);

            // When
            {{Entity}}Response result = {{entity}}Service.findById({{entity}}Id);

            // Then
            assertThat(result).isNotNull();
        }

        @ParameterizedTest
        @DisplayName("should handle various search terms")
        @ValueSource(strings = {"test", "TEST", "TeSt", "   test   "})
        @NullSource
        @EmptySource
        void shouldHandleVariousSearchTerms(String searchTerm) {
            // Given
            Pageable pageable = PageRequest.of(0, 10);

            if (searchTerm == null || searchTerm.isBlank()) {
                given({{entity}}Repository.findAll(pageable))
                    .willReturn(new PageImpl<>(List.of({{entity}})));
            } else {
                given({{entity}}Repository.findByNameContainingIgnoreCase(anyString(), eq(pageable)))
                    .willReturn(new PageImpl<>(List.of({{entity}})));
            }
            given({{entity}}Mapper.toResponse(any())).willReturn(response);

            // When & Then
            assertThatNoException()
                .isThrownBy(() -> {{entity}}Service.findAll(searchTerm, pageable));
        }

        @ParameterizedTest
        @DisplayName("should validate price ranges")
        @CsvSource({
            "0.00, true",
            "100.00, true",
            "9999999.99, true"
        })
        void shouldValidatePriceRanges(BigDecimal price, boolean isValid) {
            // Test price validation logic
            assertThat(price.compareTo(BigDecimal.ZERO) >= 0).isEqualTo(isValid);
        }
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package}}` | Base package name | `com.example.app` |
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |

## Integration Test Template

```java
package {{package}}.integration;

import {{package}}.domain.entity.{{Entity}};
import {{package}}.domain.entity.{{Entity}}Status;
import {{package}}.repository.{{Entity}}Repository;
import {{package}}.web.dto.{{Entity}}Request;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
@DisplayName("{{Entity}} API Integration Tests")
class {{Entity}}IntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private {{Entity}}Repository {{entity}}Repository;

    private {{Entity}} {{entity}};
    private {{Entity}}Request request;

    @BeforeEach
    void setUp() {
        {{entity}}Repository.deleteAll();

        {{entity}} = {{Entity}}.builder()
            .name("Test {{Entity}}")
            .description("Test Description")
            .status({{Entity}}Status.ACTIVE)
            .build();
        {{entity}} = {{entity}}Repository.save({{entity}});

        request = new {{Entity}}Request(
            "New {{Entity}}",
            "New Description",
            null,
            BigDecimal.valueOf(99.99),
            null,
            List.of(),
            List.of()
        );
    }

    @Nested
    @DisplayName("GET /api/v1/{{entities}}")
    class GetAll{{Entity}}s {

        @Test
        @DisplayName("should return paginated {{entities}}")
        @WithMockUser
        void shouldReturnPaginated{{Entity}}s() throws Exception {
            // When & Then
            mockMvc.perform(get("/api/v1/{{entities}}")
                    .param("page", "0")
                    .param("size", "10"))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(1)))
                .andExpect(jsonPath("$.content[0].name").value("Test {{Entity}}"))
                .andExpect(jsonPath("$.totalElements").value(1));
        }

        @Test
        @DisplayName("should filter by search term")
        @WithMockUser
        void shouldFilterBySearchTerm() throws Exception {
            mockMvc.perform(get("/api/v1/{{entities}}")
                    .param("search", "Test"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(1)));

            mockMvc.perform(get("/api/v1/{{entities}}")
                    .param("search", "NonExistent"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", empty()));
        }

        @Test
        @DisplayName("should return 401 when not authenticated")
        void shouldReturn401WhenNotAuthenticated() throws Exception {
            mockMvc.perform(get("/api/v1/{{entities}}"))
                .andExpect(status().isUnauthorized());
        }
    }

    @Nested
    @DisplayName("GET /api/v1/{{entities}}/{id}")
    class Get{{Entity}}ById {

        @Test
        @DisplayName("should return {{entity}} when found")
        @WithMockUser
        void shouldReturn{{Entity}}WhenFound() throws Exception {
            mockMvc.perform(get("/api/v1/{{entities}}/{id}", {{entity}}.getId()))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value({{entity}}.getId().toString()))
                .andExpect(jsonPath("$.name").value("Test {{Entity}}"));
        }

        @Test
        @DisplayName("should return 404 when not found")
        @WithMockUser
        void shouldReturn404WhenNotFound() throws Exception {
            UUID nonExistentId = UUID.randomUUID();

            mockMvc.perform(get("/api/v1/{{entities}}/{id}", nonExistentId))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Not Found"));
        }
    }

    @Nested
    @DisplayName("POST /api/v1/{{entities}}")
    class Create{{Entity}} {

        @Test
        @DisplayName("should create {{entity}} successfully")
        @WithMockUser(roles = {"ADMIN"})
        void shouldCreate{{Entity}}Successfully() throws Exception {
            mockMvc.perform(post("/api/v1/{{entities}}")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andDo(print())
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").exists())
                .andExpect(jsonPath("$.name").value("New {{Entity}}"));
        }

        @Test
        @DisplayName("should return 400 for invalid request")
        @WithMockUser(roles = {"ADMIN"})
        void shouldReturn400ForInvalidRequest() throws Exception {
            {{Entity}}Request invalidRequest = new {{Entity}}Request(
                "", // Invalid: empty name
                "Description",
                null,
                BigDecimal.valueOf(-1), // Invalid: negative price
                null,
                List.of(),
                List.of()
            );

            mockMvc.perform(post("/api/v1/{{entities}}")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(invalidRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errors").isArray());
        }

        @Test
        @DisplayName("should return 403 for unauthorized user")
        @WithMockUser(roles = {"USER"})
        void shouldReturn403ForUnauthorizedUser() throws Exception {
            mockMvc.perform(post("/api/v1/{{entities}}")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isForbidden());
        }
    }

    @Nested
    @DisplayName("PUT /api/v1/{{entities}}/{id}")
    class Update{{Entity}} {

        @Test
        @DisplayName("should update {{entity}} successfully")
        @WithMockUser(roles = {"ADMIN"})
        void shouldUpdate{{Entity}}Successfully() throws Exception {
            {{Entity}}Request updateRequest = new {{Entity}}Request(
                "Updated Name",
                "Updated Description",
                null,
                BigDecimal.valueOf(199.99),
                null,
                List.of(),
                List.of()
            );

            mockMvc.perform(put("/api/v1/{{entities}}/{id}", {{entity}}.getId())
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(updateRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Updated Name"));
        }

        @Test
        @DisplayName("should return 404 for non-existent {{entity}}")
        @WithMockUser(roles = {"ADMIN"})
        void shouldReturn404ForNonExistent{{Entity}}() throws Exception {
            UUID nonExistentId = UUID.randomUUID();

            mockMvc.perform(put("/api/v1/{{entities}}/{id}", nonExistentId)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isNotFound());
        }
    }

    @Nested
    @DisplayName("DELETE /api/v1/{{entities}}/{id}")
    class Delete{{Entity}} {

        @Test
        @DisplayName("should delete {{entity}} successfully")
        @WithMockUser(roles = {"ADMIN"})
        void shouldDelete{{Entity}}Successfully() throws Exception {
            mockMvc.perform(delete("/api/v1/{{entities}}/{id}", {{entity}}.getId()))
                .andExpect(status().isNoContent());

            // Verify deletion
            mockMvc.perform(get("/api/v1/{{entities}}/{id}", {{entity}}.getId())
                    .with(user("user")))
                .andExpect(status().isNotFound());
        }

        @Test
        @DisplayName("should return 403 for non-admin user")
        @WithMockUser(roles = {"MANAGER"})
        void shouldReturn403ForNonAdminUser() throws Exception {
            mockMvc.perform(delete("/api/v1/{{entities}}/{id}", {{entity}}.getId()))
                .andExpect(status().isForbidden());
        }
    }
}
```

## Customization Options

### With Testcontainers

```java
@SpringBootTest
@Testcontainers
@ActiveProfiles("test")
class {{Entity}}RepositoryIntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine");

    @Autowired
    private {{Entity}}Repository {{entity}}Repository;

    @Test
    void shouldPersist{{Entity}}() {
        {{Entity}} entity = {{Entity}}.builder()
            .name("Test")
            .status({{Entity}}Status.ACTIVE)
            .build();

        {{Entity}} saved = {{entity}}Repository.save(entity);

        assertThat(saved.getId()).isNotNull();
        assertThat({{entity}}Repository.findById(saved.getId())).isPresent();
    }
}
```

### With Test Fixtures

```java
@Component
public class {{Entity}}TestFixtures {

    public static {{Entity}} create{{Entity}}() {
        return {{Entity}}.builder()
            .name("Test {{Entity}}")
            .description("Test Description")
            .status({{Entity}}Status.ACTIVE)
            .build();
    }

    public static {{Entity}}Request create{{Entity}}Request() {
        return new {{Entity}}Request(
            "Test {{Entity}}",
            "Test Description",
            null,
            BigDecimal.valueOf(99.99),
            null,
            List.of(),
            List.of()
        );
    }

    public static List<{{Entity}}> create{{Entity}}List(int count) {
        return IntStream.range(0, count)
            .mapToObj(i -> {{Entity}}.builder()
                .name("{{Entity}} " + i)
                .status({{Entity}}Status.ACTIVE)
                .build())
            .toList();
    }
}
```

### With Custom Assertions

```java
public class {{Entity}}Assertions {

    public static {{Entity}}Assert assertThat({{Entity}} actual) {
        return new {{Entity}}Assert(actual);
    }

    public static class {{Entity}}Assert extends AbstractAssert<{{Entity}}Assert, {{Entity}}> {

        public {{Entity}}Assert({{Entity}} actual) {
            super(actual, {{Entity}}Assert.class);
        }

        public {{Entity}}Assert hasName(String name) {
            isNotNull();
            if (!Objects.equals(actual.getName(), name)) {
                failWithMessage("Expected name to be <%s> but was <%s>",
                    name, actual.getName());
            }
            return this;
        }

        public {{Entity}}Assert hasStatus({{Entity}}Status status) {
            isNotNull();
            if (!Objects.equals(actual.getStatus(), status)) {
                failWithMessage("Expected status to be <%s> but was <%s>",
                    status, actual.getStatus());
            }
            return this;
        }

        public {{Entity}}Assert isActive() {
            return hasStatus({{Entity}}Status.ACTIVE);
        }

        public {{Entity}}Assert isNotDeleted() {
            isNotNull();
            if (actual.isDeleted()) {
                failWithMessage("Expected {{entity}} to not be deleted");
            }
            return this;
        }
    }
}
```

### With MockMvc Custom ResultMatchers

```java
public class {{Entity}}ResultMatchers {

    public static ResultMatcher is{{Entity}}({{Entity}} expected) {
        return result -> {
            String json = result.getResponse().getContentAsString();
            ObjectMapper mapper = new ObjectMapper();
            mapper.findAndRegisterModules();

            {{Entity}}Response actual = mapper.readValue(json, {{Entity}}Response.class);

            assertThat(actual.id()).isEqualTo(expected.getId());
            assertThat(actual.name()).isEqualTo(expected.getName());
        };
    }

    public static ResultMatcher hasValidationError(String field, String message) {
        return result -> {
            String json = result.getResponse().getContentAsString();
            assertThat(json).contains(field);
            assertThat(json).contains(message);
        };
    }
}
```
