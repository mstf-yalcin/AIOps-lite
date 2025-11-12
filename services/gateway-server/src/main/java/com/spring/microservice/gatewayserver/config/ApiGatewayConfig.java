package com.spring.microservice.gatewayserver.config;

import org.springframework.cloud.gateway.filter.ratelimit.KeyResolver;
import org.springframework.cloud.gateway.filter.ratelimit.RedisRateLimiter;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.concurrent.TimeoutException;

@Configuration
public class ApiGatewayConfig {

    @Bean
    public RouteLocator gatewayRoutes(RouteLocatorBuilder builder) {
        return builder.routes()
                .route(p -> p.path("/gateway/accounts/**")
                        .filters(f -> f.rewritePath("/gateway/accounts/(?<segment>.*)", "/${segment}")
                                .addResponseHeader("X-Response-Time", LocalDateTime.now().toString())
                                .circuitBreaker(c -> c.setName("accountsCircuitBreaker")
                                        .setFallbackUri("forward:/accountServiceFallback")))
                        .uri("lb://ACCOUNTS"))
                .route(p -> p.path("/gateway/cards/**")
                        .filters(f -> f.rewritePath("/gateway/cards/(?<segment>.*)", "/${segment}")
                                .addResponseHeader("X-Response-Time", LocalDateTime.now().toString())
                                .retry(r -> r.setRetries(3)
                                        .setMethods(HttpMethod.GET)
                                        .setExceptions(TimeoutException.class)
                                        .setBackoff(Duration.ofMillis(100), Duration.ofMillis(1000), 2, true)))
                        .uri("lb://CARDS"))
                .route(p -> p.path("/gateway/loans/**")
                        .filters(f -> f.rewritePath("/gateway/loans/(?<segment>.*)", "/${segment}")
                                .addResponseHeader("X-Response-Time", LocalDateTime.now().toString())

                                .requestRateLimiter(c -> c.setRateLimiter(redisRateLimiter())
                                        .setKeyResolver(userKeyResolver())))

                        .uri("lb://loans"))
                .build();
    }


    @Bean
    public RedisRateLimiter redisRateLimiter() {
        return new RedisRateLimiter(1, 5, 5);
    }

    @Bean
    KeyResolver userKeyResolver() {
        return exchange -> Mono.justOrEmpty(exchange.getRequest().getQueryParams().getFirst("user"))
                .defaultIfEmpty("anonymous");
    }

}