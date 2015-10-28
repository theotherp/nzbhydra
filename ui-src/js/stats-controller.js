angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope) {


    $scope.options = {
        chart: {
            type: 'lineChart',
            x: function (d) {
                return d.x;
            },
            y: function (d) {
                return d.y;
            },

            xAxis: {
                axisLabel: 'Index'
            },
            yAxis: {
                axisLabel: 'Response time (ms)'
            }
        }


    };

    var s = [{
        "response_time": 417
    },
        {
            "response_time": 336
        },
        {
            "response_time": 7
        },
        {
            "response_time": 6
        },
        {
            "response_time": 6
        },
        {
            "response_time": 6
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 8
        },
        {
            "response_time": 703
        },
        {
            "response_time": 621
        },
        {
            "response_time": 262
        },
        {
            "response_time": 294
        },
        {
            "response_time": 275
        },
        {
            "response_time": 312
        },
        {
            "response_time": 320
        },
        {
            "response_time": 339
        },
        {
            "response_time": 200
        },
        {
            "response_time": 352
        },
        {
            "response_time": 192
        },
        {
            "response_time": 877
        },
        {
            "response_time": 254
        },
        {
            "response_time": 6
        },
        {
            "response_time": 4
        },
        {
            "response_time": 293
        },
        {
            "response_time": 822
        },
        {
            "response_time": 304
        },
        {
            "response_time": 3
        },
        {
            "response_time": 218
        },
        {
            "response_time": 371
        },
        {
            "response_time": 200
        },
        {
            "response_time": 250
        },
        {
            "response_time": 297
        },
        {
            "response_time": 344
        },
        {
            "response_time": 231
        },
        {
            "response_time": 11
        },
        {
            "response_time": 285
        },
        {
            "response_time": 258
        },
        {
            "response_time": 19
        },
        {
            "response_time": 117
        },
        {
            "response_time": 421
        },
        {
            "response_time": 15
        },
        {
            "response_time": 9
        },
        {
            "response_time": 429
        },
        {
            "response_time": 10
        },
        {
            "response_time": 200
        },
        {
            "response_time": 19
        },
        {
            "response_time": 12
        },
        {
            "response_time": 818
        },
        {
            "response_time": 258
        },
        {
            "response_time": 21
        },
        {
            "response_time": 9
        },
        {
            "response_time": 336
        },
        {
            "response_time": 19
        },
        {
            "response_time": 412
        },
        {
            "response_time": 304
        },
        {
            "response_time": 18
        },
        {
            "response_time": 184
        },
        {
            "response_time": 8
        },
        {
            "response_time": 27
        },
        {
            "response_time": 19
        },
        {
            "response_time": 390
        },
        {
            "response_time": 258
        },
        {
            "response_time": 245
        },
        {
            "response_time": 468
        },
        {
            "response_time": 14
        },
        {
            "response_time": 51
        },
        {
            "response_time": 66
        },
        {
            "response_time": 25
        },
        {
            "response_time": 19
        },
        {
            "response_time": 37
        },
        {
            "response_time": 23
        },
        {
            "response_time": 56
        },
        {
            "response_time": 53
        },
        {
            "response_time": 45
        },
        {
            "response_time": 81
        },
        {
            "response_time": 53
        },
        {
            "response_time": 124
        },
        {
            "response_time": 126
        },
        {
            "response_time": 112
        },
        {
            "response_time": 68
        },
        {
            "response_time": 40
        },
        {
            "response_time": 106
        },
        {
            "response_time": 110
        },
        {
            "response_time": 48
        },
        {
            "response_time": 67
        },
        {
            "response_time": 76
        },
        {
            "response_time": 85
        },
        {
            "response_time": 100
        },
        {
            "response_time": 40
        },
        {
            "response_time": 78
        },
        {
            "response_time": 74
        },
        {
            "response_time": 74
        },
        {
            "response_time": 118
        },
        {
            "response_time": 73
        },
        {
            "response_time": 60
        },
        {
            "response_time": 70
        },
        {
            "response_time": 37
        },
        {
            "response_time": 36
        },
        {
            "response_time": 716
        },
        {
            "response_time": 247
        },
        {
            "response_time": 10
        },
        {
            "response_time": 368
        },
        {
            "response_time": 7
        },
        {
            "response_time": 8
        },
        {
            "response_time": 10
        },
        {
            "response_time": 11
        },
        {
            "response_time": 256
        },
        {
            "response_time": 306
        },
        {
            "response_time": 256
        },
        {
            "response_time": 273
        },
        {
            "response_time": 5
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 7
        },
        {
            "response_time": 7
        },
        {
            "response_time": 6
        },
        {
            "response_time": 6
        },
        {
            "response_time": 6
        },
        {
            "response_time": 5
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 6
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 24
        },
        {
            "response_time": 5
        },
        {
            "response_time": 6
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 8
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 8
        },
        {
            "response_time": 7
        },
        {
            "response_time": 7
        },
        {
            "response_time": 7
        },
        {
            "response_time": 8
        },
        {
            "response_time": 7
        },
        {
            "response_time": 7
        },
        {
            "response_time": 11
        },
        {
            "response_time": 329
        },
        {
            "response_time": 9
        },
        {
            "response_time": 11
        },
        {
            "response_time": 9
        },
        {
            "response_time": 11
        },
        {
            "response_time": 325
        },
        {
            "response_time": 11
        },
        {
            "response_time": 6
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 7
        },
        {
            "response_time": 6
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 6
        },
        {
            "response_time": 21
        },
        {
            "response_time": 7
        },
        {
            "response_time": 274
        },
        {
            "response_time": 255
        },
        {
            "response_time": 7
        },
        {
            "response_time": 12
        },
        {
            "response_time": 301
        },
        {
            "response_time": 11
        },
        {
            "response_time": 8
        },
        {
            "response_time": 241
        },
        {
            "response_time": 10
        },
        {
            "response_time": 366
        },
        {
            "response_time": 7
        },
        {
            "response_time": 14
        },
        {
            "response_time": 232
        },
        {
            "response_time": 8
        },
        {
            "response_time": 261
        },
        {
            "response_time": 14
        },
        {
            "response_time": 9
        },
        {
            "response_time": 834
        },
        {
            "response_time": 22
        },
        {
            "response_time": 272
        },
        {
            "response_time": 325
        },
        {
            "response_time": 19
        },
        {
            "response_time": 261
        },
        {
            "response_time": 10
        },
        {
            "response_time": 286
        },
        {
            "response_time": 308
        },
        {
            "response_time": 12
        },
        {
            "response_time": 362
        },
        {
            "response_time": 23
        },
        {
            "response_time": 391
        },
        {
            "response_time": 310
        },
        {
            "response_time": 980
        },
        {
            "response_time": 223
        },
        {
            "response_time": 288
        },
        {
            "response_time": 273
        },
        {
            "response_time": 5
        },
        {
            "response_time": 249
        },
        {
            "response_time": 7
        },
        {
            "response_time": 243
        },
        {
            "response_time": 5
        },
        {
            "response_time": 264
        },
        {
            "response_time": 6
        },
        {
            "response_time": 13
        },
        {
            "response_time": 354
        },
        {
            "response_time": 233
        },
        {
            "response_time": 8
        },
        {
            "response_time": 296
        },
        {
            "response_time": 7
        },
        {
            "response_time": 266
        },
        {
            "response_time": 6
        },
        {
            "response_time": 247
        },
        {
            "response_time": 8
        },
        {
            "response_time": 284
        },
        {
            "response_time": 251
        },
        {
            "response_time": 222
        },
        {
            "response_time": 9
        },
        {
            "response_time": 343
        },
        {
            "response_time": 266
        },
        {
            "response_time": 236
        },
        {
            "response_time": 266
        },
        {
            "response_time": 243
        },
        {
            "response_time": 221
        },
        {
            "response_time": 301
        },
        {
            "response_time": 250
        },
        {
            "response_time": 234
        },
        {
            "response_time": 298
        },
        {
            "response_time": 234
        },
        {
            "response_time": 11
        },
        {
            "response_time": 318
        },
        {
            "response_time": 10
        },
        {
            "response_time": 983
        },
        {
            "response_time": 270
        },
        {
            "response_time": 301
        },
        {
            "response_time": 24
        },
        {
            "response_time": 9
        },
        {
            "response_time": 8
        },
        {
            "response_time": 14
        },
        {
            "response_time": 17
        },
        {
            "response_time": 318
        },
        {
            "response_time": 281
        },
        {
            "response_time": 24
        },
        {
            "response_time": 20
        },
        {
            "response_time": 24
        },
        {
            "response_time": 19
        },
        {
            "response_time": 25
        },
        {
            "response_time": 13
        },
        {
            "response_time": 19
        },
        {
            "response_time": 12
        },
        {
            "response_time": 8
        },
        {
            "response_time": 10
        },
        {
            "response_time": 9
        },
        {
            "response_time": 18
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 11
        },
        {
            "response_time": 14
        },
        {
            "response_time": 9
        },
        {
            "response_time": 27
        },
        {
            "response_time": 15
        },
        {
            "response_time": 10
        },
        {
            "response_time": 9
        },
        {
            "response_time": 13
        },
        {
            "response_time": 10
        },
        {
            "response_time": 10
        },
        {
            "response_time": 9
        },
        {
            "response_time": 13
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 775
        },
        {
            "response_time": 246
        },
        {
            "response_time": 7
        },
        {
            "response_time": 248
        },
        {
            "response_time": 7
        },
        {
            "response_time": 212
        },
        {
            "response_time": 269
        },
        {
            "response_time": 307
        },
        {
            "response_time": 11
        },
        {
            "response_time": 9
        },
        {
            "response_time": 13
        },
        {
            "response_time": 442
        },
        {
            "response_time": 13
        },
        {
            "response_time": 263
        },
        {
            "response_time": 303
        },
        {
            "response_time": 261
        },
        {
            "response_time": 328
        },
        {
            "response_time": 344
        },
        {
            "response_time": 290
        },
        {
            "response_time": 14
        },
        {
            "response_time": 19
        },
        {
            "response_time": 17
        },
        {
            "response_time": 14
        },
        {
            "response_time": 19
        },
        {
            "response_time": 836
        },
        {
            "response_time": 285
        },
        {
            "response_time": 11
        },
        {
            "response_time": 13
        },
        {
            "response_time": 11
        },
        {
            "response_time": 821
        },
        {
            "response_time": 11
        },
        {
            "response_time": 17
        },
        {
            "response_time": 404
        },
        {
            "response_time": 12
        },
        {
            "response_time": 9
        },
        {
            "response_time": 10
        },
        {
            "response_time": 350
        },
        {
            "response_time": 677
        },
        {
            "response_time": 9
        },
        {
            "response_time": 247
        },
        {
            "response_time": 257
        },
        {
            "response_time": 214
        },
        {
            "response_time": 422
        },
        {
            "response_time": 293
        },
        {
            "response_time": 212
        },
        {
            "response_time": 227
        },
        {
            "response_time": 8
        },
        {
            "response_time": 283
        },
        {
            "response_time": 204
        },
        {
            "response_time": 295
        },
        {
            "response_time": 7
        },
        {
            "response_time": 6
        },
        {
            "response_time": 188
        },
        {
            "response_time": 355
        },
        {
            "response_time": 192
        },
        {
            "response_time": 17
        },
        {
            "response_time": 765
        },
        {
            "response_time": 340
        },
        {
            "response_time": 298
        },
        {
            "response_time": 477
        },
        {
            "response_time": 274
        },
        {
            "response_time": 6
        },
        {
            "response_time": 7
        },
        {
            "response_time": 260
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 272
        },
        {
            "response_time": 14
        },
        {
            "response_time": 7
        },
        {
            "response_time": 230
        },
        {
            "response_time": 18
        },
        {
            "response_time": 760
        },
        {
            "response_time": 191
        },
        {
            "response_time": 8
        },
        {
            "response_time": 10
        },
        {
            "response_time": 239
        },
        {
            "response_time": 322
        },
        {
            "response_time": 342
        },
        {
            "response_time": 654
        },
        {
            "response_time": 267
        },
        {
            "response_time": 323
        },
        {
            "response_time": 13
        },
        {
            "response_time": 388
        },
        {
            "response_time": 896
        },
        {
            "response_time": 270
        },
        {
            "response_time": 406
        },
        {
            "response_time": 305
        },
        {
            "response_time": 419
        },
        {
            "response_time": 17
        },
        {
            "response_time": 572
        },
        {
            "response_time": 270
        },
        {
            "response_time": 270
        },
        {
            "response_time": 23
        },
        {
            "response_time": 7
        },
        {
            "response_time": 7
        },
        {
            "response_time": 18
        },
        {
            "response_time": 398
        },
        {
            "response_time": 12
        },
        {
            "response_time": 12
        },
        {
            "response_time": 333
        },
        {
            "response_time": 20
        },
        {
            "response_time": 10
        },
        {
            "response_time": 375
        },
        {
            "response_time": 696
        },
        {
            "response_time": 8
        },
        {
            "response_time": 565
        },
        {
            "response_time": 9
        },
        {
            "response_time": 22
        },
        {
            "response_time": 18
        },
        {
            "response_time": 9
        },
        {
            "response_time": 10
        },
        {
            "response_time": 16
        },
        {
            "response_time": 29
        },
        {
            "response_time": 333
        },
        {
            "response_time": 52
        },
        {
            "response_time": 10
        },
        {
            "response_time": 9
        },
        {
            "response_time": 12
        },
        {
            "response_time": 9
        },
        {
            "response_time": 11
        },
        {
            "response_time": 10
        },
        {
            "response_time": 23
        },
        {
            "response_time": 9
        },
        {
            "response_time": 19
        },
        {
            "response_time": 16
        },
        {
            "response_time": 10
        },
        {
            "response_time": 17
        },
        {
            "response_time": 10
        },
        {
            "response_time": 11
        },
        {
            "response_time": 17
        },
        {
            "response_time": 16
        },
        {
            "response_time": 10
        },
        {
            "response_time": 24
        },
        {
            "response_time": 16
        },
        {
            "response_time": 22
        },
        {
            "response_time": 9
        },
        {
            "response_time": 14
        },
        {
            "response_time": 893
        },
        {
            "response_time": 253
        },
        {
            "response_time": 346
        },
        {
            "response_time": 41
        },
        {
            "response_time": 354
        },
        {
            "response_time": 240
        },
        {
            "response_time": 252
        },
        {
            "response_time": 212
        },
        {
            "response_time": 826
        },
        {
            "response_time": 458
        },
        {
            "response_time": 9
        },
        {
            "response_time": 241
        },
        {
            "response_time": 317
        },
        {
            "response_time": 336
        },
        {
            "response_time": 382
        },
        {
            "response_time": 374
        },
        {
            "response_time": 417
        },
        {
            "response_time": 19
        },
        {
            "response_time": 17
        },
        {
            "response_time": 19
        },
        {
            "response_time": 818
        },
        {
            "response_time": 10
        },
        {
            "response_time": 5
        },
        {
            "response_time": 105
        },
        {
            "response_time": 372
        },
        {
            "response_time": 378
        },
        {
            "response_time": 421
        },
        {
            "response_time": 320
        },
        {
            "response_time": 309
        },
        {
            "response_time": 249
        },
        {
            "response_time": 701
        },
        {
            "response_time": 33
        },
        {
            "response_time": 22
        },
        {
            "response_time": 312
        },
        {
            "response_time": 697
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 9
        },
        {
            "response_time": 223
        },
        {
            "response_time": 937
        },
        {
            "response_time": 250
        },
        {
            "response_time": 329
        },
        {
            "response_time": 7
        },
        {
            "response_time": 13
        },
        {
            "response_time": 326
        },
        {
            "response_time": 14
        },
        {
            "response_time": 12
        },
        {
            "response_time": 328
        },
        {
            "response_time": 7
        },
        {
            "response_time": 475
        },
        {
            "response_time": 12
        },
        {
            "response_time": 9
        },
        {
            "response_time": 311
        },
        {
            "response_time": 221
        },
        {
            "response_time": 228
        },
        {
            "response_time": 230
        },
        {
            "response_time": 263
        },
        {
            "response_time": 206
        },
        {
            "response_time": 224
        },
        {
            "response_time": 267
        },
        {
            "response_time": 236
        },
        {
            "response_time": 244
        },
        {
            "response_time": 213
        },
        {
            "response_time": 227
        },
        {
            "response_time": 709
        },
        {
            "response_time": 288
        },
        {
            "response_time": 301
        },
        {
            "response_time": 253
        },
        {
            "response_time": 620
        },
        {
            "response_time": 240
        },
        {
            "response_time": 699
        },
        {
            "response_time": 238
        },
        {
            "response_time": 251
        },
        {
            "response_time": 269
        },
        {
            "response_time": 250
        },
        {
            "response_time": 270
        },
        {
            "response_time": 287
        },
        {
            "response_time": 364
        },
        {
            "response_time": 665
        },
        {
            "response_time": 252
        },
        {
            "response_time": 14
        },
        {
            "response_time": 7
        },
        {
            "response_time": 393
        },
        {
            "response_time": 266
        },
        {
            "response_time": 250
        },
        {
            "response_time": 274
        },
        {
            "response_time": 408
        },
        {
            "response_time": 442
        },
        {
            "response_time": 230
        },
        {
            "response_time": 768
        },
        {
            "response_time": 663
        },
        {
            "response_time": 254
        },
        {
            "response_time": 680
        },
        {
            "response_time": 333
        },
        {
            "response_time": 695
        },
        {
            "response_time": 251
        },
        {
            "response_time": 271
        },
        {
            "response_time": 306
        },
        {
            "response_time": 276
        },
        {
            "response_time": 293
        },
        {
            "response_time": 312
        },
        {
            "response_time": 292
        },
        {
            "response_time": 429
        }
    ];


    $scope.data = [{
        key: "v", values: [{x: 1, y: 102}
        ]
    }];

    //var s = [{x: 1, y: 200}, {x: 10, y: 900}];
    var count = 0;
    var s = _.map(s, function(i) {
        return {x: count++, y: i.response_time}
    });
    console.log(s);

    $scope.data = [{key: "v", values: s}];
    

}
