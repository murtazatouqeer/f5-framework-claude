# Rails Controller Generator Agent

Agent for generating Rails API controllers with best practices.

## Capabilities

- Generate RESTful API controllers
- Apply authentication and authorization
- Handle pagination and filtering
- Implement proper error handling
- Follow Rails conventions

## Input Schema

```yaml
entity_name: string      # Singular entity name (e.g., "Product")
namespace: string        # API namespace (default: "Api::V1")
actions: array           # Actions to generate (default: all CRUD)
authentication: boolean  # Require authentication (default: true)
authorization: boolean   # Use Pundit policies (default: true)
pagination: boolean      # Enable pagination (default: true)
search: boolean         # Enable search/filtering (default: true)
```

## Output

Generates a complete API controller with:
- Strong parameters
- Before actions
- CRUD actions
- Error handling
- JSON responses

## Example Usage

```yaml
entity_name: Product
namespace: Api::V1
actions: [index, show, create, update, destroy]
authentication: true
authorization: true
pagination: true
search: true
```

## Generated Code Template

```ruby
# app/controllers/api/v1/{{entities}}_controller.rb
module Api
  module V1
    class {{Entities}}Controller < BaseController
      before_action :authenticate_user!
      before_action :set_{{entity}}, only: %i[show update destroy]

      # GET /api/v1/{{entities}}
      def index
        authorize {{Entity}}

        @{{entities}} = {{Entity}}Query.new
          .call(query_params)
          .includes(:category)
          .page(params[:page])
          .per(params[:per_page] || 20)

        render json: {{Entity}}Serializer.new(
          @{{entities}},
          pagination_meta(@{{entities}})
        )
      end

      # GET /api/v1/{{entities}}/:id
      def show
        authorize @{{entity}}
        render json: {{Entity}}Serializer.new(@{{entity}}, include: [:category])
      end

      # POST /api/v1/{{entities}}
      def create
        authorize {{Entity}}

        result = {{Entities}}::Create{{Entity}}.new(
          params: {{entity}}_params,
          current_user: current_user
        ).call

        if result.success?
          render json: {{Entity}}Serializer.new(result.data), status: :created
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      # PATCH/PUT /api/v1/{{entities}}/:id
      def update
        authorize @{{entity}}

        result = {{Entities}}::Update{{Entity}}.new(
          {{entity}}: @{{entity}},
          params: {{entity}}_params
        ).call

        if result.success?
          render json: {{Entity}}Serializer.new(result.data)
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      # DELETE /api/v1/{{entities}}/:id
      def destroy
        authorize @{{entity}}
        @{{entity}}.destroy!
        head :no_content
      end

      private

      def set_{{entity}}
        @{{entity}} = {{Entity}}.find(params[:id])
      end

      def {{entity}}_params
        params.require(:{{entity}}).permit(
          :name,
          :description,
          # Add permitted attributes
        )
      end

      def query_params
        params.permit(:q, :status, :sort_by, :sort_order)
      end

      def pagination_meta(collection)
        {
          meta: {
            total: collection.total_count,
            pages: collection.total_pages,
            page: collection.current_page,
            per_page: collection.limit_value
          }
        }
      end
    end
  end
end
```

## Related Files Generated

1. `app/controllers/api/v1/{{entities}}_controller.rb` - Controller
2. `spec/requests/api/v1/{{entities}}_spec.rb` - Request specs
3. `config/routes.rb` - Route entry (manual addition)

## Conventions

- Controllers are namespaced under `Api::V1`
- Use service objects for complex operations
- Use serializers for JSON responses
- Use Pundit for authorization
- Use Kaminari for pagination

## Best Practices Applied

- Thin controllers, fat services
- Strong parameters for mass assignment protection
- Proper HTTP status codes
- Consistent JSON response format
- Request specs over controller specs
