package com.spring.microservices.accounts;

import com.spring.microservices.accounts.dto.AccountsContactInfoDto;
import io.swagger.v3.oas.annotations.ExternalDocumentation;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeIn;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Contact;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.info.License;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

@SpringBootApplication
@EnableFeignClients
@EnableJpaAuditing(auditorAwareRef = "auditAware")
@OpenAPIDefinition(info = @Info(
		title = "Accounts microservice Rest API DOC",
		description = "Accounts microservice Rest API DOC",
		version = "v1.0",
		contact = @Contact(
				name = "Test", email = "test@gmail", url = "test.com"),
		license = @License(
				name = "Apache 2.0", url = "http://www.apache.org/licenses/LICENSE-2.0.html"
		)),
		externalDocs = @ExternalDocumentation(
		description = "Accounts microservice Wiki",
		url = "external.com"),
		security=@SecurityRequirement(name="bearerAuth")
)
@SecurityScheme
		(name = "bearer-key", description = "Jwt auth desc", scheme = "bearer", type = SecuritySchemeType.HTTP,
				bearerFormat = "JWT", in = SecuritySchemeIn.HEADER)

//@EnableConfigurationProperties(AccountsContactInfoDto.class)
public class AccountsApplication {

	public static void main(String[] args) {
		SpringApplication.run(AccountsApplication.class, args);
	}

}
