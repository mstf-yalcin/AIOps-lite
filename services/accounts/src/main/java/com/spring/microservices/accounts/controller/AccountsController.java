package com.spring.microservices.accounts.controller;

import com.spring.microservices.accounts.constants.AccountsConstants;
import com.spring.microservices.accounts.dto.*;
import com.spring.microservices.accounts.service.AccountsService;
import io.github.resilience4j.bulkhead.annotation.Bulkhead;
import io.github.resilience4j.ratelimiter.annotation.RateLimiter;
import io.github.resilience4j.retry.annotation.Retry;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Tag(
        name = "CRUD REST APIs for Accounts",
        description = "CRUD REST APIs to CREATE, UPDATE, FETCH AND DELETE account details"
)
@RestController
@RequestMapping(path = "/api")
public class AccountsController {

    Logger logger= LoggerFactory.getLogger(AccountsController.class);
    private final AccountsService accountsService;
    private final AccountsContactInfoDto accountsContactInfoDto;

    public AccountsController(AccountsService accountsService, AccountsContactInfoDto accountsContactInfoDto) {
        this.accountsService = accountsService;
        this.accountsContactInfoDto = accountsContactInfoDto;
    }

    @Operation(
            summary = "Create Account REST API",
            description = "REST API to create new Customer & Account"
    )
    @ApiResponses({
            @ApiResponse(
                    responseCode = "201",
                    description = "HTTP Status CREATED"
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "HTTP Status Internal Server Error",
                    content = @Content(
                            schema = @Schema(implementation = ErrorResponseDto.class)
                    )
            )
    }
    )
    @PostMapping("/create")
    public ResponseEntity<ResponseDto> createAccount(@Valid @RequestBody CustomerDto customerDto) {
        CustomerDto savedCustomerDto = accountsService.create(customerDto);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(new ResponseDto(AccountsConstants.STATUS_201, AccountsConstants.MESSAGE_201, savedCustomerDto));
    }

    @Operation(
            summary = "Fetch Account Details REST API",
            description = "REST API to fetch Customer &  Account details based on a mobile number"
    )
    @ApiResponses({
            @ApiResponse(
                    responseCode = "200",
                    description = "HTTP Status OK"
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "HTTP Status Internal Server Error",
                    content = @Content(
                            schema = @Schema(implementation = ErrorResponseDto.class)
                    )
            )
    }
    )
    @GetMapping("/fetch")
    public ResponseEntity<CustomerDto> fetchAccountDetails(@RequestParam
                                                           @Pattern(regexp = "(^$|[0-9]{10})", message = "Mobile number must be 10 digits")
                                                           String mobileNumber) {
        CustomerDto customerDto = accountsService.getCustomerByMobileNumber(mobileNumber);
        return ResponseEntity.status(HttpStatus.OK).body(customerDto);
    }

    @Operation(
            summary = "Update Account Details REST API",
            description = "REST API to update Customer &  Account details based on a account number"
    )
    @ApiResponses({
            @ApiResponse(
                    responseCode = "200",
                    description = "HTTP Status OK"
            ),
            @ApiResponse(
                    responseCode = "417",
                    description = "Expectation Failed"
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "HTTP Status Internal Server Error",
                    content = @Content(
                            schema = @Schema(implementation = ErrorResponseDto.class)
                    )
            )
    }
    )
    @PutMapping("/update")
    public ResponseEntity<ResponseDto> updateAccountDetails(@Valid @RequestBody CustomerDto customerDto) {
        CustomerDto updatedCustomer = accountsService.updateAccount(customerDto);
        return ResponseEntity
                .status(HttpStatus.OK)
                .body(new ResponseDto(AccountsConstants.STATUS_200, AccountsConstants.MESSAGE_200, updatedCustomer));

    }

    @Operation(
            summary = "Delete Account & Customer Details REST API",
            description = "REST API to delete Customer &  Account details based on a mobile number"
    )
    @ApiResponses({
            @ApiResponse(
                    responseCode = "200",
                    description = "HTTP Status OK"
            ),
            @ApiResponse(
                    responseCode = "417",
                    description = "Expectation Failed"
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "HTTP Status Internal Server Error",
                    content = @Content(
                            schema = @Schema(implementation = ErrorResponseDto.class)
                    )
            )
    }
    )
    @DeleteMapping("/delete")
    public ResponseEntity<ResponseDto> deleteAccountDetails(@RequestParam
                                                            @Pattern(regexp = "(^$|[0-9]{10})", message = "Mobile number must be 10 digits")
                                                            String mobileNumber) {
        boolean isDeleted = accountsService.deleteAccount(mobileNumber);
        if (isDeleted) {
            return ResponseEntity
                    .status(HttpStatus.OK)
                    .body(new ResponseDto(AccountsConstants.STATUS_200, AccountsConstants.MESSAGE_200, null));
        } else {
            return ResponseEntity
                    .status(HttpStatus.EXPECTATION_FAILED)
                    .body(new ResponseDto(AccountsConstants.STATUS_417, AccountsConstants.MESSAGE_417_DELETE, null));
        }
    }


    @Retry(name = "retryAccounts", fallbackMethod = "fallbackContactInfo")
    @GetMapping("/contact-info")
    public ResponseEntity<AccountsContactInfoDto> getContactInfo() {
        logger.debug("getContactInfo() method called");
        throw new NullPointerException("Exception occurred");
//        return ResponseEntity.ok(accountsContactInfoDto);
    }
    public ResponseEntity<AccountsContactInfoDto> fallbackContactInfo(Exception e) {
        logger.debug("fallbackContactInfo() method called");
        return ResponseEntity.ok(new AccountsContactInfoDto("NA", Map.of("NA","NA"),List.of("NA")));
    }


    @GetMapping("/test")
    @RateLimiter(name = "testRateLimiter",fallbackMethod = "testFallback")
    public ResponseEntity<String> test() {
        return ResponseEntity.ok("test");
    }

    public ResponseEntity<String> testFallback(Throwable e) {
        return ResponseEntity.ok("testFallback");
    }


    @GetMapping("/bulk/{data}")
    @Bulkhead(name = "custom")
    public String bulkRetrieveExchangeValue(@PathVariable String data) {
        logger.info("Called bulk endpoint Data: {}", data);
        return data;
    }





}
